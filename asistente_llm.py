"""Modulo de asistente LLM para Streamlit - Chat + Resumenes automaticos."""

import streamlit as st
from llm_utils import generar_resumen_restaurante, consultar_chat


def generar_contexto_resumen(df_reviews, df_clusters):
    df_agg = df_reviews.groupby("restaurante").agg(
        rating=("rating", "mean"),
        resenas=("rating", "count"),
        positivo=("sentimiento", lambda x: (x == "positivo").mean() * 100),
    ).round(2)
    contexto = f"Total resenas: {len(df_reviews)}\n"
    contexto += f"Total restaurantes: {df_clusters.shape[0]}\n"
    for _, r in df_agg.iterrows():
        contexto += f"- {r.name}: rating {r['rating']}, {r['resenas']} resenas, {r['positivo']}% positivas\n"
    return contexto


def mostrar_chat(df_reviews, df_clusters):
    if "mensajes" not in st.session_state:
        st.session_state.mensajes = []

    contexto = generar_contexto_resumen(df_reviews, df_clusters)

    for msg in st.session_state.mensajes:
        with st.chat_message(msg["rol"]):
            st.markdown(msg["contenido"])

    if prompt := st.chat_input("Haz una pregunta sobre los datos..."):
        st.session_state.mensajes.append({"rol": "user", "contenido": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analizando datos..."):
                respuesta = consultar_chat(prompt, contexto)
                if respuesta:
                    st.markdown(respuesta)
                    st.session_state.mensajes.append({"rol": "assistant", "contenido": respuesta})
                else:
                    st.warning("No hay LLM configurado. Configura una API key en .env")
                    st.info("Soporta: Anthropic, OpenAI, Gemini, o Groq")


def mostrar_resumen_restaurante(df_reviews, restaurante):
    df_rest = df_reviews[df_reviews["restaurante"] == restaurante]
    if df_rest.empty:
        return

    stats = {
        "rating_promedio": f"{df_rest['rating'].mean():.2f}",
    }
    sent_comida = df_rest["sentimiento_comida"].value_counts().to_dict() if "sentimiento_comida" in df_rest.columns else {}
    sent_servicio = df_rest["sentimiento_servicio"].value_counts().to_dict() if "sentimiento_servicio" in df_rest.columns else {}
    sent_precio = df_rest["sentimiento_precio"].value_counts().to_dict() if "sentimiento_precio" in df_rest.columns else {}

    key_resumen = f"resumen_{restaurante}"
    version_key = f"resumen_version_{restaurante}"
    if key_resumen not in st.session_state:
        st.session_state[key_resumen] = None
        st.session_state[version_key] = df_rest.shape[0]

    if st.session_state[key_resumen] is None or st.session_state[version_key] != df_rest.shape[0]:
        with st.spinner("Generando resumen automatico..."):
            resumen = generar_resumen_restaurante(
                restaurante, stats, df_rest.shape[0],
                sent_comida, sent_servicio, sent_precio
            )
            if resumen:
                st.session_state[key_resumen] = resumen
                st.session_state[version_key] = df_rest.shape[0]

    if st.session_state[key_resumen]:
        st.markdown(st.session_state[key_resumen])
    else:
        st.info("Configura una API key de LLM en .env para ver resumenes automaticos.")
