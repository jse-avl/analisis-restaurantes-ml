"""Paso 2: Limpieza y transformación de datos.
Genera: data/reviews_clean.csv
"""

import os
import csv
import re

RUTA_ENTRADA = os.path.join(os.path.dirname(__file__), "data", "reviews.csv")
RUTA_SALIDA = os.path.join(os.path.dirname(__file__), "data", "reviews_clean.csv")


def limpiar_texto(texto):
    texto = re.sub(r'[^\w\sáéíóúüñÁÉÍÓÚÜÑ.,;:!¿?¡()\-]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def clasificar_rating(rating):
    r = float(rating)
    if r <= 2.0:
        return "malo"
    elif r <= 3.5:
        return "neutral"
    else:
        return "bueno"


def main():
    with open(RUTA_ENTRADA, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        filas = list(reader)

    print(f"Total filas: {len(filas)}")

    limpias = []
    for row in filas:
        restaurante = row.get("restaurante", "").strip()
        rating = row.get("rating", "").strip()
        resena = row.get("reseña", "").strip()
        fecha = row.get("fecha", "").strip()

        if not restaurante:
            continue
        if not rating:
            continue

        try:
            rating_num = float(rating)
        except (ValueError, TypeError):
            continue

        if not resena or resena == "Sin reseña disponible":
            continue

        resena_limpia = limpiar_texto(resena)
        if len(resena_limpia) < 5:
            continue

        limpias.append({
            "restaurante": restaurante,
            "categoria": row.get("categoria", "").strip(),
            "barrio": row.get("barrio", "").strip(),
            "rating": rating_num,
            "reseña_limpia": resena_limpia,
            "longitud_reseña": len(resena_limpia),
            "categoria_rating": clasificar_rating(rating_num),
            "sentimiento": row.get("sentimiento", "").strip().lower(),
            "fecha": fecha
        })

    vistos = set()
    unicas = []
    for row in limpias:
        clave = (row["restaurante"], row["reseña_limpia"][:50])
        if clave not in vistos:
            vistos.add(clave)
            unicas.append(row)

    print(f"Después de limpiar: {len(unicas)} reseñas únicas")

    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    campos = ["restaurante", "categoria", "barrio", "rating", "reseña_limpia",
              "longitud_reseña", "categoria_rating", "sentimiento", "fecha"]
    with open(RUTA_SALIDA, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(unicas)

    print(f"Limpieza completada. {len(unicas)} reseñas guardadas.")


if __name__ == "__main__":
    main()
