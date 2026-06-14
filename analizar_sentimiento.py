"""Paso 3: Análisis de sentimiento por aspecto con LLM (Claude/OpenAI) o respaldo.
Genera: data/reviews_con_sentimiento.csv
"""

import os
import csv
import json
import re
from dotenv import load_dotenv

load_dotenv()

RUTA_ENTRADA = os.path.join(os.path.dirname(__file__), "data", "reviews_clean.csv")
RUTA_SALIDA = os.path.join(os.path.dirname(__file__), "data", "reviews_con_sentimiento.csv")

# ---- Palabras clave por aspecto ----

PALABRAS_COMIDA_POS = [
    "delicioso", "sabroso", "rico", "rica", "ricos", "ricas", "exquisito",
    "fresco", "fresca", "sabrosa", "sabrosas", "sabroso", "buenísimo",
    "riquísimo", "excelente", "espectacular", "perfecto", "impecable",
    "calidad", "frescos", "frescas", "pulpo", "langosta", "ceviche",
    "pescado", "innovador", "variedad", "sabores", "sazón", "sazon",
    "jugoso", "tierno", "bien preparado", "bien cocido",
]
PALABRAS_COMIDA_NEG = [
    "salado", "salada", "quemado", "quemada", "frío", "fría", "insípido",
    "insípida", "desabrido", "desabrida", "duro", "dura", "grasiento",
    "grasienta", "asqueroso", "intragable", "incomible", "soso", "sosa",
    "crudo", "cruda", "mal cocido", "reciclado", "recalentado",
]
PALABRAS_SERVICIO_POS = [
    "amable", "atento", "atenta", "atentos", "atentas", "rápido", "rápida",
    "eficiente", "servicial", "serviciales", "simpático", "simpática",
    "cortés", "profesional", "excelente atención", "buen servicio",
    "nos atendieron", "recomendó", "explicó",
]
PALABRAS_SERVICIO_NEG = [
    "lento", "lenta", "lentos", "descortés", "ignoró", "tardó",
    "grosero", "grosera", "maleducado", "irrespetuoso", "mal servicio",
    "desorganizado", "desordenado", "no atendieron", "espera",
    "demora", "demoró", "demorado", "esperando", "esperé",
]
PALABRAS_PRECIO_POS = [
    "barato", "económico", "accesible", "precio justo", "buen precio",
    "vale la pena", "relación calidad", "bien de precio", "baratísimo",
]
PALABRAS_PRECIO_NEG = [
    "caro", "cara", "caros", "caras", "carísimo", "carísima",
    "sobreprecio", "sobrevalorado", "cobran", "cobró", "caro para",
    "no vale", "excesivo", "costoso",
]

POSITIVAS_ES = PALABRAS_COMIDA_POS + PALABRAS_SERVICIO_POS + PALABRAS_PRECIO_POS + [
    "excelente", "increíble", "espectacular", "perfecto", "maravilloso",
    "fantástico", "encantó", "recomiendo", "fabuloso", "genial",
    "magnífico", "estupendo", "sensacional", "gratamente", "mejor",
    "encanta", "cómodo", "agradable", "feliz", "contento",
    "sorprendió", "bien", "buena", "bueno", "buenos", "buenas",
    "delicia", "encantadora", "encantador", "divertido", "divertida",
    "tranquilo", "tranquila", "lindo", "linda", "bonito", "bonita",
    "increible", "bellísimo", "hermoso", "hermosa", "inolvidable",
    "grato", "grata", "acogedor", "acogedora", "esmero", "buenísima",
    "excelentes", "perfectas", "perfectos", "recomendado", "recomendada",
    "recomendados", "recomendadas", "recomendable", "valió", "valio",
    "vale", "maravillosa", "maravilloso", "precioso", "preciosa",
    "especial", "único", "única", "placentero", "placentera",
    "satisfecho", "satisfecha", "encantan", "encantó", "encanta",
    "encantaron", "fascinó", "fascina", "cálido", "cálida",
    "limpio", "limpia", "higiénico", "variado", "variada",
]

NEGATIVAS_ES = PALABRAS_COMIDA_NEG + PALABRAS_SERVICIO_NEG + PALABRAS_PRECIO_NEG + [
    "malo", "mala", "malos", "malas", "pésimo", "pésima", "terrible",
    "horrible", "fatal", "decepcionante", "decepción", "decepcionó",
    "sucio", "sucia", "ruidoso", "ruidosa", "peor", "nunca",
    "no vuelvo", "no regreso", "desagradable", "incómodo", "incómoda",
    "feo", "fea", "desastre", "horroroso", "horrorosa", "triste",
    "aburrido", "aburrida", "insuficiente", "mediocre", "pobre",
    "deficiente", "equivocaron", "error", "errores", "equivocado",
    "no me gustó", "no gustó", "no me gusta", "no recomiendo",
    "no volvería", "no vuelvo", "peor", "pésima experiencia",
    "mala experiencia",
]

NEUTRALES_ES = [
    "regular", "normal", "correcto", "promedio", "aceptable", "pasable",
    "más o menos", "tal cual", "estándar", "suficiente", "decente",
    "ok", "okay", "está bien", "esta bien",
]


def analizar_sentimiento_keyword(texto):
    texto_lower = texto.lower()
    pos_count = sum(1 for p in POSITIVAS_ES if p in texto_lower)
    neg_count = sum(1 for n in NEGATIVAS_ES if n in texto_lower)

    if pos_count > neg_count:
        return "positivo", pos_count - neg_count
    elif neg_count > pos_count:
        return "negativo", neg_count - pos_count
    else:
        return "neutral", 0


def analizar_aspecto_keyword(texto, palabras_pos, palabras_neg):
    texto_lower = texto.lower()
    pos = sum(1 for p in palabras_pos if p in texto_lower)
    neg = sum(1 for n in palabras_neg if n in texto_lower)
    if pos > neg:
        return "positivo"
    elif neg > pos:
        return "negativo"
    return "neutral"


def extraer_palabras_clave(texto, palabras_referencia, max_palabras=3):
    texto_lower = texto.lower()
    encontradas = [p for p in palabras_referencia if p in texto_lower]
    return encontradas[:max_palabras]


def analizar_con_llm(texto, usar_openai=False):
    if usar_openai:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            prompt = f"""Analiza esta reseña de restaurante y extrae el sentimiento por ASPECTO.

Reseña: {texto}

Responde SOLO en JSON con esta estructura exacta:
{{
  "sentimiento_general": "positivo|neutral|negativo",
  "comida": "positivo|neutral|negativo",
  "servicio": "positivo|neutral|negativo",
  "precio": "positivo|neutral|negativo",
  "palabras_clave_comida": ["palabra1", "palabra2"],
  "palabras_clave_servicio": ["palabra1", "palabra2"],
  "palabras_clave_precio": ["palabra1", "palabra2"]
}}"""
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(resp.choices[0].message.content)
        except Exception as e:
            print(f"Error con OpenAI: {e}")
            return None
    else:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            prompt = f"""Analiza esta reseña de restaurante y extrae el sentimiento por ASPECTO.

Reseña: {texto}

Responde SOLO en JSON (sin markdown, solo JSON) con esta estructura exacta:
{{
  "sentimiento_general": "positivo|neutral|negativo",
  "comida": "positivo|neutral|negativo",
  "servicio": "positivo|neutral|negativo",
  "precio": "positivo|neutral|negativo",
  "palabras_clave_comida": ["palabra1", "palabra2"],
  "palabras_clave_servicio": ["palabra1", "palabra2"],
  "palabras_clave_precio": ["palabra1", "palabra2"]
}}"""
            resp = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )
            texto_json = resp.content[0].text.strip()
            if texto_json.startswith("```"):
                texto_json = re.sub(r'^```(?:json)?\n?', '', texto_json)
                texto_json = re.sub(r'\n?```$', '', texto_json)
            return json.loads(texto_json)
        except Exception as e:
            print(f"Error con Claude: {e}")
            return None


def main():
    if not os.path.exists(RUTA_ENTRADA):
        print(f"ERROR: No se encuentra {RUTA_ENTRADA}")
        return

    with open(RUTA_ENTRADA, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        filas = list(reader)

    print(f"Analizando {len(filas)} reseñas...")

    usar_llm = False
    usar_openai = False
    if os.getenv("ANTHROPIC_API_KEY") and os.getenv("ANTHROPIC_API_KEY") != "tu_api_key_aqui":
        usar_llm = True
        print("Usando Claude API para análisis de sentimiento...")
    elif os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "tu_api_key_aqui":
        usar_llm = True
        usar_openai = True
        print("Usando OpenAI API para análisis de sentimiento...")
    else:
        print("No hay LLM API key. Usando análisis por palabras clave...")

    resultados = []
    for i, row in enumerate(filas):
        texto = row.get("reseña_limpia", row.get("reseña", ""))
        sentimiento_previo = row.get("sentimiento", "").strip().lower()

        if usar_llm and i < 50:
            result = analizar_con_llm(texto, usar_openai)
            if result:
                sentimiento = result.get("sentimiento_general", "neutral")

                def aspect_val(val):
                    v = str(val).lower().strip()
                    return v if v in ("positivo", "neutral", "negativo") else "neutral"

                sent_comida = aspect_val(result.get("comida", "neutral"))
                sent_servicio = aspect_val(result.get("servicio", "neutral"))
                sent_precio = aspect_val(result.get("precio", "neutral"))
                comida_kw = ", ".join(result.get("palabras_clave_comida", [])) if isinstance(result.get("palabras_clave_comida"), list) else ""
                servicio_kw = ", ".join(result.get("palabras_clave_servicio", [])) if isinstance(result.get("palabras_clave_servicio"), list) else ""
                precio_kw = ", ".join(result.get("palabras_clave_precio", [])) if isinstance(result.get("palabras_clave_precio"), list) else ""
            else:
                sentimiento, _ = analizar_sentimiento_keyword(texto)
                sent_comida = analizar_aspecto_keyword(texto, PALABRAS_COMIDA_POS, PALABRAS_COMIDA_NEG)
                sent_servicio = analizar_aspecto_keyword(texto, PALABRAS_SERVICIO_POS, PALABRAS_SERVICIO_NEG)
                sent_precio = analizar_aspecto_keyword(texto, PALABRAS_PRECIO_POS, PALABRAS_PRECIO_NEG)
                comida_kw = ""
                servicio_kw = ""
                precio_kw = ""
        else:
            if usar_llm and i >= 50:
                print(f"  Límite LLM alcanzado (50), usando keyword para resto...")

            if sentimiento_previo in ("positivo", "neutral", "negativo"):
                sentimiento = sentimiento_previo
                _, confianza = analizar_sentimiento_keyword(texto)
            else:
                sentimiento, _ = analizar_sentimiento_keyword(texto)

            sent_comida = analizar_aspecto_keyword(texto, PALABRAS_COMIDA_POS, PALABRAS_COMIDA_NEG)
            sent_servicio = analizar_aspecto_keyword(texto, PALABRAS_SERVICIO_POS, PALABRAS_SERVICIO_NEG)
            sent_precio = analizar_aspecto_keyword(texto, PALABRAS_PRECIO_POS, PALABRAS_PRECIO_NEG)
            comida_kw = ", ".join(extraer_palabras_clave(texto, PALABRAS_COMIDA_POS + PALABRAS_COMIDA_NEG)) if sent_comida != "neutral" else ""
            servicio_kw = ", ".join(extraer_palabras_clave(texto, PALABRAS_SERVICIO_POS + PALABRAS_SERVICIO_NEG)) if sent_servicio != "neutral" else ""
            precio_kw = ", ".join(extraer_palabras_clave(texto, PALABRAS_PRECIO_POS + PALABRAS_PRECIO_NEG)) if sent_precio != "neutral" else ""

        resultados.append({
            "restaurante": row["restaurante"],
            "categoria": row.get("categoria", ""),
            "barrio": row.get("barrio", ""),
            "rating": row["rating"],
            "reseña": texto,
            "longitud_reseña": row.get("longitud_reseña", len(texto)),
            "categoria_rating": row.get("categoria_rating", ""),
            "sentimiento": sentimiento,
            "sentimiento_comida": sent_comida,
            "sentimiento_servicio": sent_servicio,
            "sentimiento_precio": sent_precio,
            "palabras_clave_comida": comida_kw,
            "palabras_clave_servicio": servicio_kw,
            "palabras_clave_precio": precio_kw,
            "fecha": row.get("fecha", "")
        })

        if (i + 1) % 50 == 0:
            print(f"  Procesadas {i + 1}/{len(filas)} reseñas")

    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    campos = ["restaurante", "categoria", "barrio", "rating", "reseña",
              "longitud_reseña", "categoria_rating", "sentimiento",
              "sentimiento_comida", "sentimiento_servicio", "sentimiento_precio",
              "palabras_clave_comida", "palabras_clave_servicio", "palabras_clave_precio",
              "fecha"]
    with open(RUTA_SALIDA, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)

    sent_count = {}
    for r in resultados:
        s = r["sentimiento"]
        sent_count[s] = sent_count.get(s, 0) + 1
    print(f"Distribución de sentimiento: {sent_count}")

    for aspecto in ("comida", "servicio", "precio"):
        col = f"sentimiento_{aspecto}"
        counts = {}
        for r in resultados:
            v = r.get(col, "neutral")
            counts[v] = counts.get(v, 0) + 1
        print(f"  {aspecto}: {counts}")

    print(f"Análisis completado. {len(resultados)} reseñas guardadas.")


if __name__ == "__main__":
    main()
