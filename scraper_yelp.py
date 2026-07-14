import os
import csv
import time
import requests
from dotenv import load_dotenv

load_dotenv()

RUTA_DATA = os.path.join(os.path.dirname(__file__), "data")
API_KEY = os.getenv("YELP_API_KEY", "")
API_URL = "https://api.yelp.com/v3"

HEADERS = {"Authorization": f"Bearer {API_KEY}"}


def buscar_restaurantes(ubicacion="Panama", limite=50):
    resultados = []
    for offset in range(0, limite, 20):
        resp = requests.get(
            f"{API_URL}/businesses/search",
            headers=HEADERS,
            params={
                "location": ubicacion,
                "term": "restaurants",
                "limit": min(20, limite - offset),
                "offset": offset,
            },
            timeout=15,
        )
        if resp.status_code != 200:
            print(f"  Error Yelp search: {resp.status_code} {resp.text[:200]}")
            break
        data = resp.json()
        resultados.extend(data.get("businesses", []))
        print(f"  Offset {offset}: {len(data.get('businesses', []))} negocios")
        if len(resultados) >= limite:
            break
        time.sleep(0.5)
    return resultados


def obtener_resenas(business_id, max_reviews=3):
    resp = requests.get(
        f"{API_URL}/businesses/{business_id}/reviews",
        headers=HEADERS,
        timeout=15,
    )
    if resp.status_code != 200:
        return []
    data = resp.json()
    return data.get("reviews", [])[:max_reviews]


def main():
    if not API_KEY or API_KEY == "tu_yelp_api_key_aqui":
        print("ERROR: YELP_API_KEY no configurada en .env")
        print("Registrate en https://www.yelp.com/developers para obtener una key gratuita")
        return

    print("=== Scraper Yelp Fusion API ===")
    restaurantes = buscar_restaurantes()
    print(f"Encontrados {len(restaurantes)} restaurantes")

    todas_resenas = []
    for i, r in enumerate(restaurantes):
        nombre = r.get("name", "")
        resenas = obtener_resenas(r["id"])
        for rev in resenas:
            todas_resenas.append({
                "restaurante": f"{nombre} (Yelp)",
                "categoria": ", ".join(c["title"] for c in r.get("categories", [])),
                "barrio": r.get("location", {}).get("city", ""),
                "rating": rev.get("rating", 0),
                "reseña": rev.get("text", ""),
                "sentimiento": "",
                "fecha": rev.get("time_created", ""),
            })
        if (i + 1) % 10 == 0:
            print(f"  Procesados {i+1}/{len(restaurantes)} restaurantes ({len(todas_resenas)} resenas)")
        time.sleep(0.3)

    os.makedirs(RUTA_DATA, exist_ok=True)
    salida = os.path.join(RUTA_DATA, "reviews_yelp.csv")
    campos = ["restaurante", "categoria", "barrio", "rating", "reseña", "sentimiento", "fecha"]
    with open(salida, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(todas_resenas)
    print(f"\nTotal resenas Yelp: {len(todas_resenas)}")
    print(f"Guardado en: {salida}")


if __name__ == "__main__":
    main()
