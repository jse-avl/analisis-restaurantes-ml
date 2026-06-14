"""Paso 4: Clustering de restaurantes con KMeans.
Genera: data/clusters.csv
"""

import os
import csv
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

RUTA_ENTRADA = os.path.join(os.path.dirname(__file__), "data", "reviews_con_sentimiento.csv")
RUTA_SALIDA = os.path.join(os.path.dirname(__file__), "data", "clusters.csv")


def main():
    if not os.path.exists(RUTA_ENTRADA):
        print(f"ERROR: No se encuentra {RUTA_ENTRADA}")
        return

    with open(RUTA_ENTRADA, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        filas = list(reader)

    print(f"Cargadas {len(filas)} reseñas con sentimiento")

    stats = {}
    for row in filas:
        rest = row["restaurante"]
        if rest not in stats:
            stats[rest] = {"ratings": [], "sentimientos": [], "conteo": 0}
        stats[rest]["ratings"].append(float(row["rating"]))
        stats[rest]["sentimientos"].append(row["sentimiento"])
        stats[rest]["conteo"] += 1

    datos = []
    for rest, s in stats.items():
        ratings = s["ratings"]
        sentimientos = s["sentimientos"]
        total = len(ratings)
        pos_pct = sentimientos.count("positivo") / total * 100 if total > 0 else 0
        datos.append({
            "restaurante": rest,
            "rating_promedio": round(np.mean(ratings), 2),
            "num_resenas": total,
            "pct_positivo": round(pos_pct, 1),
            "pct_neutral": round(sentimientos.count("neutral") / total * 100, 1),
            "pct_negativo": round(sentimientos.count("negativo") / total * 100, 1),
            "popularidad": total
        })

    print(f"\nResumen de {len(datos)} restaurantes:")
    for d in sorted(datos, key=lambda x: x["rating_promedio"], reverse=True):
        print(f"  {d['restaurante']:20s} | rating {d['rating_promedio']:.1f} | {d['num_resenas']:2d} resenas | {d['pct_positivo']:5.1f}% positivas")

    X = np.array([[d["rating_promedio"], d["num_resenas"], d["pct_positivo"]] for d in datos])
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n_clusters = min(4, len(datos) - 1)
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = kmeans.fit_predict(X_scaled)

    # Compute quality of each cluster centroid and assign labels
    centroids = scaler.inverse_transform(kmeans.cluster_centers_)
    cluster_quality = {}
    for i, centroid in enumerate(centroids):
        rating, num_resenas, pct_pos = centroid
        score = rating * 0.4 + pct_pos * 0.6 / 100 * 5
        cluster_quality[i] = score

    # Sort cluster indices by quality (descending)
    sorted_clusters = sorted(cluster_quality.keys(), key=lambda k: cluster_quality[k], reverse=True)
    quality_labels = ["Excelente", "Bueno", "Regular", "Malo"]
    cluster_names = {}
    for rank, cluster_id in enumerate(sorted_clusters):
        cluster_names[cluster_id] = quality_labels[rank] if rank < len(quality_labels) else f"Cluster {rank}"

    for i, d in enumerate(datos):
        d["cluster"] = cluster_names.get(labels[i], f"Cluster {labels[i]}")

    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    campos = ["restaurante", "rating_promedio", "num_resenas",
              "pct_positivo", "pct_neutral", "pct_negativo",
              "popularidad", "cluster"]
    with open(RUTA_SALIDA, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(datos)

    print(f"\n--- Clusters ---")
    for d in sorted(datos, key=lambda x: x["cluster"]):
        print(f"  [{d['cluster']:10s}] {d['restaurante']:20s} | rating {d['rating_promedio']:.1f} | {d['pct_positivo']:.1f}% positivo")

    print(f"\nClustering completado. {len(datos)} restaurantes en {n_clusters} clusters.")


if __name__ == "__main__":
    main()
