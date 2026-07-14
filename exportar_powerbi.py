"""Paso 6: Exportar datos a esquema estrella para Power BI.
Genera: data/powerbi/ (5 CSVs en formato estrella)
El archivo .pbix se genera solo una vez (si no existe).
"""

import os
import subprocess
import sys
import pandas as pd
from datetime import datetime

RUTA_DATA = os.path.join(os.path.dirname(__file__), "data")
RUTA_SENTIMIENTO = os.path.join(RUTA_DATA, "reviews_con_sentimiento.csv")
RUTA_CLUSTERS = os.path.join(RUTA_DATA, "clusters.csv")
RUTA_PBI = os.path.join(RUTA_DATA, "powerbi")
RUTA_PBIX = os.path.join(RUTA_PBI, "RestaurantReviews.pbix")
COMPILADO_CSharp = os.path.join(os.path.dirname(__file__), "tools", "BuildPBIX.exe")


def generar_id_fecha(fecha_str):
    if not fecha_str:
        return 1
    dt = None
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%B %Y", "%Y-%m-%dT%H:%M:%S"]:
        try:
            dt = datetime.strptime(fecha_str.strip(), fmt)
            break
        except ValueError:
            continue
    if dt is None:
        dt = parse_fecha_relativa(fecha_str)
    if dt is None:
        return 1
    return int(dt.strftime("%Y%m%d"))


def parse_fecha_relativa(fecha_str):
    import re
    from datetime import timedelta
    ahora = datetime(2026, 7, 13)
    fecha_lower = fecha_str.strip().lower()
    match = re.search(r'hace\s+(\d+)\s+(dia|dias|semana|semanas|mes|meses|año|anos|year|years)', fecha_lower)
    if not match:
        return None
    cantidad = int(match.group(1))
    unidad = match.group(2)
    if unidad in ("dia", "dias", "day", "days"):
        return ahora - timedelta(days=cantidad)
    elif unidad in ("semana", "semanas", "week", "weeks"):
        return ahora - timedelta(weeks=cantidad)
    elif unidad in ("mes", "meses", "month", "months"):
        mes = ahora.month - cantidad
        anio = ahora.year
        while mes <= 0:
            mes += 12
            anio -= 1
        dia = min(ahora.day, 28)
        return datetime(anio, mes, dia)
    elif unidad in ("año", "anos", "year", "years"):
        return datetime(ahora.year - cantidad, ahora.month, min(ahora.day, 28))
    return None


def extraer_fecha_components(fecha_str):
    if not fecha_str:
        return {"año": 0, "mes": 0, "dia": 0, "dia_semana": 0, "nombre_dia": "Desconocido",
                "nombre_mes": "Desconocido", "trimestre": 0}
    dt = None
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%B %Y", "%Y-%m-%dT%H:%M:%S"]:
        try:
            dt = datetime.strptime(fecha_str.strip(), fmt)
            break
        except ValueError:
            continue
    if dt is None:
        dt = parse_fecha_relativa(fecha_str)
    if dt is None:
        return {"año": 0, "mes": 0, "dia": 0, "dia_semana": 0, "nombre_dia": "Desconocido",
                "nombre_mes": "Desconocido", "trimestre": 0}
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
             "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    return {
        "año": dt.year,
        "mes": dt.month,
        "dia": dt.day,
        "dia_semana": dt.weekday() + 1,
        "nombre_dia": dias[dt.weekday()],
        "nombre_mes": meses[dt.month - 1],
        "trimestre": (dt.month - 1) // 3 + 1,
    }


def main():
    if not os.path.exists(RUTA_SENTIMIENTO):
        print(f"ERROR: No se encuentra {RUTA_SENTIMIENTO}")
        return

    df = pd.read_csv(RUTA_SENTIMIENTO)
    df_clusters = pd.read_csv(RUTA_CLUSTERS) if os.path.exists(RUTA_CLUSTERS) else pd.DataFrame()

    os.makedirs(RUTA_PBI, exist_ok=True)

    rest_data = df.groupby("restaurante").agg(
        rating_promedio=("rating", "mean"),
        num_resenas=("rating", "count"),
        pct_positivo=("sentimiento", lambda x: (x == "positivo").mean() * 100),
        categoria=("categoria", "first"),
        barrio=("barrio", "first"),
    ).reset_index()

    if not df_clusters.empty:
        cluster_map = df_clusters[["restaurante", "cluster"]].set_index("restaurante")["cluster"].to_dict()
        rest_data["cluster"] = rest_data["restaurante"].map(cluster_map).fillna("No asignado")

    rest_data["id_restaurante"] = range(1, len(rest_data) + 1)
    rest_data.to_csv(os.path.join(RUTA_PBI, "DimRestaurante.csv"), index=False, encoding="utf-8")
    print(f"DimRestaurante: {len(rest_data)} restaurantes")

    fechas_unicas = df["fecha"].dropna().unique()
    fecha_rows = []
    seen_fechas = set()
    for f in fechas_unicas:
        id_f = generar_id_fecha(f)
        if id_f in seen_fechas:
            continue
        seen_fechas.add(id_f)
        comp = extraer_fecha_components(f)
        fecha_rows.append({
            "id_fecha": id_f,
            "fecha_completa": f,
            "año": comp["año"],
            "mes": comp["mes"],
            "nombre_mes": comp["nombre_mes"],
            "dia": comp["dia"],
            "dia_semana": comp["dia_semana"],
            "nombre_dia": comp["nombre_dia"],
            "trimestre": comp["trimestre"],
        })
    pd.DataFrame(fecha_rows).to_csv(os.path.join(RUTA_PBI, "DimFecha.csv"), index=False, encoding="utf-8")
    print(f"DimFecha: {len(fecha_rows)} fechas")

    sent_rows = []
    seen_sent = set()
    for _, row in df.iterrows():
        clave = (row.get("sentimiento", ""), row.get("sentimiento_comida", ""),
                 row.get("sentimiento_servicio", ""), row.get("sentimiento_precio", ""))
        if clave not in seen_sent:
            seen_sent.add(clave)
    for i, clave in enumerate(seen_sent, 1):
        sent_rows.append({
            "id_sentimiento": i,
            "sentimiento_general": clave[0],
            "sentimiento_comida": clave[1],
            "sentimiento_servicio": clave[2],
            "sentimiento_precio": clave[3],
        })
    pd.DataFrame(sent_rows).to_csv(os.path.join(RUTA_PBI, "DimSentimiento.csv"), index=False, encoding="utf-8")
    print(f"DimSentimiento: {len(sent_rows)} combinaciones")

    rating_rows = []
    for r in sorted(df["rating"].unique()):
        cat = "malo" if r <= 2 else "neutral" if r <= 3.5 else "bueno"
        rating_rows.append({
            "id_rating": int(r),
            "rating_numerico": r,
            "categoria_rating": cat,
        })
    pd.DataFrame(rating_rows).to_csv(os.path.join(RUTA_PBI, "DimRating.csv"), index=False, encoding="utf-8")
    print(f"DimRating: {len(rating_rows)} ratings")

    rest_id_map = rest_data.set_index("restaurante")["id_restaurante"].to_dict()
    sent_map = {}
    for s in sent_rows:
        sent_map[(s["sentimiento_general"], s["sentimiento_comida"],
                  s["sentimiento_servicio"], s["sentimiento_precio"])] = s["id_sentimiento"]

    fact_rows = []
    for i, (_, row) in enumerate(df.iterrows(), 1):
        clave_sent = (row.get("sentimiento", ""), row.get("sentimiento_comida", ""),
                      row.get("sentimiento_servicio", ""), row.get("sentimiento_precio", ""))
        fact_rows.append({
            "id_resena": i,
            "id_restaurante": rest_id_map.get(row["restaurante"], 1),
            "id_fecha": generar_id_fecha(row.get("fecha", "")),
            "id_sentimiento": sent_map.get(clave_sent, 1),
            "id_rating": int(row["rating"]),
            "rating": row["rating"],
            "longitud_reseña": len(str(row.get("reseña", ""))),
        })
    pd.DataFrame(fact_rows).to_csv(os.path.join(RUTA_PBI, "FactResenas.csv"), index=False, encoding="utf-8")
    print(f"FactResenas: {len(fact_rows)} resenas")

    print(f"\nExportacion completada. Archivos en: {RUTA_PBI}")

    if not os.path.exists(RUTA_PBIX):
        if os.path.exists(COMPILADO_CSharp):
            print("Generando RestaurantReviews.pbix (solo la primera vez)...")
            try:
                subprocess.run([COMPILADO_CSharp, RUTA_DATA, RUTA_PBIX], check=True, timeout=30)
                print("PBIX creado exitosamente.")
            except Exception as e:
                print(f"  No se pudo generar el .pbix: {e}")
                print("  Crea el .pbix manualmente siguiendo docs/powerbi_guide.md")
        else:
            print("  Compilado C# no encontrado. Salta generacion de .pbix.")
            print("  Crea el .pbix manualmente siguiendo docs/powerbi_guide.md")
    else:
        print(f"PBIX ya existe ({RUTA_PBIX}) — se conservan los visuales existentes")
        print("Abrelo en Power BI Desktop y haz clic en 'Actualizar' para cargar los nuevos datos")


if __name__ == "__main__":
    main()
