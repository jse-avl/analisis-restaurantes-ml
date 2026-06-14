import os
import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="Analisis de Resenas de Restaurantes - Panama",
    page_icon="🍽️",
    layout="wide"
)

RUTA_DATA = os.path.join(os.path.dirname(__file__), "data")
RUTA_REVIEWS = os.path.join(RUTA_DATA, "reviews_con_sentimiento.csv")
RUTA_CLUSTERS = os.path.join(RUTA_DATA, "clusters.csv")


@st.cache_data
def cargar_datos():
    df_reviews = pd.read_csv(RUTA_REVIEWS, encoding="utf-8")
    df_clusters = pd.read_csv(RUTA_CLUSTERS, encoding="utf-8")
    return df_reviews, df_clusters


df_reviews, df_clusters = cargar_datos()

colores_cluster = {
    "Excelente": "#2ecc71",
    "Bueno": "#3498db",
    "Regular": "#f39c12",
    "Malo": "#e74c3c"
}

st.title("🍽️ Plataforma de Analisis de Resenas de Restaurantes")
st.markdown("### Panama | Grupo 5: Christian Duraty, Yireikis Abrego, Jorge Izarra, Jose Avila")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Resumen General",
    "🔍 Analisis por Restaurante",
    "📈 Clustering",
    "⭐ Recomendaciones"
])

with tab1:
    st.header("Resumen General")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Restaurantes", df_clusters.shape[0])
    with col2:
        st.metric("Resenas Totales", df_reviews.shape[0])
    with col3:
        st.metric("Rating Promedio", f"{df_reviews['rating'].mean():.2f}")
    with col4:
        pct_pos = (df_reviews['sentimiento'].value_counts().get('positivo', 0) / df_reviews.shape[0] * 100)
        st.metric("Resenas Positivas", f"{pct_pos:.0f}%")

    st.subheader("Distribucion de Ratings")
    fig, ax = plt.subplots(figsize=(10, 4))
    df_reviews['categoria_rating'].value_counts().reindex(['bueno', 'neutral', 'malo']).plot(
        kind='bar', color=['#2ecc71', '#f39c12', '#e74c3c'], ax=ax
    )
    ax.set_xlabel("Categoria")
    ax.set_ylabel("Cantidad de Resenas")
    ax.tick_params(axis='x', rotation=0)
    st.pyplot(fig)

    st.subheader("Tabla de Restaurantes")

    col_filtro1, col_filtro2 = st.columns(2)
    with col_filtro1:
        busqueda = st.text_input("Buscar por nombre", "")
    with col_filtro2:
        rating_min, rating_max = st.slider("Rango de rating", 1.0, 5.0, (1.0, 5.0))

    df_filtrado = df_clusters.copy()
    if busqueda:
        df_filtrado = df_filtrado[df_filtrado['restaurante'].str.contains(busqueda, case=False, na=False)]
    df_filtrado = df_filtrado[
        (df_filtrado['rating_promedio'] >= rating_min) &
        (df_filtrado['rating_promedio'] <= rating_max)
    ]

    df_tabla = df_filtrado[['restaurante', 'rating_promedio', 'num_resenas',
                             'pct_positivo', 'pct_negativo', 'cluster']].copy()
    df_tabla.columns = ['Restaurante', 'Rating Prom.', '# Resenas',
                         '% Positivo', '% Negativo', 'Cluster']
    st.dataframe(df_tabla.sort_values('Rating Prom.', ascending=False),
                 use_container_width=True, hide_index=True)

with tab2:
    st.header("Analisis por Restaurante")

    restaurantes = sorted(df_reviews['restaurante'].unique())
    seleccion = st.selectbox("Selecciona un restaurante", restaurantes)

    if seleccion:
        df_rest = df_reviews[df_reviews['restaurante'] == seleccion]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Rating Promedio", f"{df_rest['rating'].mean():.2f}")
        with col2:
            st.metric("Numero de Resenas", df_rest.shape[0])
        with col3:
            pct_pos_rest = (df_rest['sentimiento'].value_counts().get('positivo', 0) / df_rest.shape[0] * 100)
            st.metric("Resenas Positivas", f"{pct_pos_rest:.0f}%")

        col_izq, col_der = st.columns(2)

        with col_izq:
            st.subheader("Distribucion de Ratings")
            fig, ax = plt.subplots(figsize=(6, 4))
            df_rest['rating'].plot(kind='hist', bins=8, color='#3498db',
                                   edgecolor='white', ax=ax)
            ax.set_xlabel("Rating")
            ax.set_ylabel("Frecuencia")
            st.pyplot(fig)

        with col_der:
            st.subheader("Distribucion de Sentimiento")
            sent_counts = df_rest['sentimiento'].value_counts()
            fig, ax = plt.subplots(figsize=(6, 4))
            colors_sent = {'positivo': '#2ecc71', 'neutral': '#f39c12', 'negativo': '#e74c3c'}
            sent_counts.plot(kind='bar',
                             color=[colors_sent.get(s, '#95a5a6') for s in sent_counts.index],
                             ax=ax)
            ax.set_xlabel("Sentimiento")
            ax.set_ylabel("Cantidad")
            ax.tick_params(axis='x', rotation=0)
            st.pyplot(fig)

        st.subheader("Sentimiento por Aspecto (LLM)")
        aspectos = ["comida", "servicio", "precio"]
        cols_aspecto = st.columns(3)
        colors_aspecto = {"positivo": "#2ecc71", "neutral": "#f39c12", "negativo": "#e74c3c"}
        for col_aspecto, aspecto in zip(cols_aspecto, aspectos):
            col_sent = f"sentimiento_{aspecto}"
            if col_sent in df_rest.columns:
                counts = df_rest[col_sent].value_counts()
                with col_aspecto:
                    st.markdown(f"**{aspecto.capitalize()}**")
                    for sent in ["positivo", "neutral", "negativo"]:
                        val = counts.get(sent, 0)
                        pct = val / df_rest.shape[0] * 100 if df_rest.shape[0] > 0 else 0
                        st.markdown(
                            f"<span style='color: {colors_aspecto.get(sent, '#95a5a6')}; font-size: 1.2em;'>"
                            f"{'✅' if sent == 'positivo' else '➖' if sent == 'neutral' else '❌'} "
                            f"{sent.capitalize()}: {val} ({pct:.0f}%)</span>",
                            unsafe_allow_html=True
                        )

        col_palabras, col_resenas = st.columns(2)

        with col_palabras:
            for aspecto, color in [("comida", "#2ecc71"), ("servicio", "#3498db"), ("precio", "#e67e22")]:
                col_kw = f"palabras_clave_{aspecto}"
                if col_kw not in df_rest.columns:
                    continue
                st.subheader(f"{aspecto.capitalize()}")
                todas = []
                for text in df_rest[col_kw].dropna():
                    todas.extend([p.strip() for p in text.split(',') if p.strip()])
                if todas:
                    freq = pd.Series(todas).value_counts().head(6)
                    fig, ax = plt.subplots(figsize=(6, 2.5))
                    freq.sort_values().plot(kind='barh', color=color, ax=ax)
                    ax.set_xlabel("Frecuencia")
                    st.pyplot(fig)
                else:
                    st.caption(f"Sin menciones especificas de {aspecto}")

        with col_resenas:
            st.subheader("Ultimas 10 resenas")
            df_ultimas = df_rest.sort_values('fecha', ascending=False).head(10)
            for _, row in df_ultimas.iterrows():
                emoji = {"positivo": "✅", "neutral": "➖", "negativo": "❌"}
                sent_emoji = emoji.get(row['sentimiento'], "❓")
                st.write(f"{sent_emoji} **{row['sentimiento'].upper()}** | ⭐ {row['rating']}")
                st.write(f"> {row['reseña'][:200]}")
                st.write(f"📅 {row['fecha']}")
                st.write("---")

with tab3:
    st.header("Clustering de Restaurantes")

    st.subheader("Grafico de Clusters")
    fig, ax = plt.subplots(figsize=(10, 6))

    for cluster in df_clusters['cluster'].unique():
        df_clust = df_clusters[df_clusters['cluster'] == cluster]
        color = colores_cluster.get(cluster, '#95a5a6')
        ax.scatter(
            df_clust['rating_promedio'],
            df_clust['pct_positivo'],
            s=df_clust['num_resenas'] * 15,
            c=color,
            label=cluster,
            alpha=0.7,
            edgecolors='black',
            linewidth=0.5
        )
        for _, row in df_clust.iterrows():
            ax.annotate(
                row['restaurante'],
                (row['rating_promedio'], row['pct_positivo']),
                fontsize=8,
                ha='center',
                va='bottom',
                xytext=(0, 5),
                textcoords='offset points'
            )

    ax.set_xlabel("Rating Promedio")
    ax.set_ylabel("% Resenas Positivas")
    ax.legend()
    ax.set_xlim(2.5, 5.5)
    ax.set_ylim(0, 100)
    st.pyplot(fig)

    st.subheader("Tabla de Restaurantes por Cluster")
    for cluster in ['Excelente', 'Bueno', 'Regular', 'Malo']:
        df_clust = df_clusters[df_clusters['cluster'] == cluster]
        if df_clust.empty:
            continue
        color = colores_cluster.get(cluster, '#95a5a6')
        st.markdown(f"<h4 style='color: {color};'>{cluster}</h4>", unsafe_allow_html=True)
        cols_show = ['restaurante', 'rating_promedio', 'num_resenas',
                      'pct_positivo', 'pct_negativo']
        st.dataframe(
            df_clust[cols_show].sort_values('rating_promedio', ascending=False),
            use_container_width=True,
            hide_index=True
        )

    st.subheader("Estadisticas por Cluster")
    stats_cluster = df_clusters.groupby('cluster').agg(
        Restaurantes=('restaurante', 'count'),
        Rating_Promedio=('rating_promedio', 'mean'),
        Total_Resenas=('num_resenas', 'sum'),
        Sentimiento_Positivo_Prom=('pct_positivo', 'mean')
    ).round(2)
    stats_cluster.columns = ['Restaurantes', 'Rating Prom.', 'Total Resenas', '% Positivo Prom.']
    st.dataframe(stats_cluster, use_container_width=True)

with tab4:
    st.header("Recomendaciones de Restaurantes")

    col_input1, col_input2 = st.columns(2)
    with col_input1:
        rating_min_req = st.slider("Rating minimo", 1.0, 5.0, 3.5, step=0.5)
    with col_input2:
        sentimiento_deseado = st.selectbox(
            "Sentimiento deseado",
            ["positivo", "neutral", "positivo o neutral"]
        )

    max_resenas = df_clusters['num_resenas'].max()

    puntuaciones = []
    for _, row in df_clusters.iterrows():
        rating_score = row['rating_promedio'] * 0.5
        sent_score = row['pct_positivo'] / 100 * 0.3
        pop_score = (row['num_resenas'] / max_resenas) * 0.2
        puntuacion = rating_score + sent_score + pop_score

        if row['rating_promedio'] < rating_min_req:
            continue

        if sentimiento_deseado == "positivo" and row['pct_positivo'] < 50:
            continue
        if sentimiento_deseado == "neutral" and row['pct_positivo'] > 70:
            continue

        puntuaciones.append({
            "Restaurante": row['restaurante'],
            "Rating Promedio": row['rating_promedio'],
            "% Positivo": row['pct_positivo'],
            "Resenas": row['num_resenas'],
            "Cluster": row['cluster'],
            "Puntuacion": round(puntuacion, 3)
        })

    df_punt = pd.DataFrame(puntuaciones)
    if not df_punt.empty:
        df_top = df_punt.sort_values('Puntuacion', ascending=False).head(5)

        st.subheader("Top 5 Restaurantes Recomendados")
        fig, ax = plt.subplots(figsize=(10, 4))
        colors_top = [colores_cluster.get(c, '#95a5a6') for c in df_top['Cluster']]
        bars = ax.barh(df_top['Restaurante'], df_top['Puntuacion'], color=colors_top)
        for i, (_, r) in enumerate(df_top.iterrows()):
            ax.text(bars[i].get_width() + 0.01, bars[i].get_y() + bars[i].get_height() / 2,
                    f" ⭐ {r['Rating Promedio']} | {r['% Positivo']:.0f}% pos",
                    va='center', fontsize=9)
        ax.set_xlabel("Puntuacion")
        ax.invert_yaxis()
        st.pyplot(fig)

        st.subheader("Detalle")
        st.dataframe(df_top, use_container_width=True, hide_index=True)
    else:
        st.warning("No hay restaurantes que cumplan con los criterios seleccionados.")
