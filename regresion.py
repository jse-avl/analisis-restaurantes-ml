"""Paso 5: Regresion - Random Forest para predecir rating.
Genera: data/regresion_metrics.json, data/regresion_resultados.csv
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder

RUTA_ENTRADA = os.path.join(os.path.dirname(__file__), "data", "reviews_con_sentimiento.csv")
RUTA_METRICAS = os.path.join(os.path.dirname(__file__), "data", "regresion_metrics.json")
RUTA_RESULTADOS = os.path.join(os.path.dirname(__file__), "data", "regresion_resultados.csv")


def main():
    if not os.path.exists(RUTA_ENTRADA):
        print(f"ERROR: No se encuentra {RUTA_ENTRADA}")
        return

    df = pd.read_csv(RUTA_ENTRADA)
    print(f"Cargadas {len(df)} resenas con sentimiento")

    df["longitud"] = df["reseña"].astype(str).str.len()
    df["sentimiento_num"] = df["sentimiento"].map({"positivo": 2, "neutral": 1, "negativo": 0})
    df["sentimiento_comida_num"] = df["sentimiento_comida"].map({"positivo": 2, "neutral": 1, "negativo": 0})
    df["sentimiento_servicio_num"] = df["sentimiento_servicio"].map({"positivo": 2, "neutral": 1, "negativo": 0})
    df["sentimiento_precio_num"] = df["sentimiento_precio"].map({"positivo": 2, "neutral": 1, "negativo": 0})

    label_enc = LabelEncoder()
    df["restaurante_id"] = label_enc.fit_transform(df["restaurante"])

    feature_cols = [
        "longitud", "sentimiento_num",
        "sentimiento_comida_num", "sentimiento_servicio_num", "sentimiento_precio_num",
        "restaurante_id"
    ]
    X = df[feature_cols].fillna(0)
    y = df["rating"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    y_pred_all = model.predict(X)

    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_test, y_pred)

    metricas = {
        "modelo": "RandomForestRegressor",
        "n_estimators": 100,
        "features": feature_cols,
        "train_samples": int(len(X_train)),
        "test_samples": int(len(X_test)),
        "mae": round(mae, 4),
        "mse": round(mse, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 4),
    }

    print(f"\n--- Metricas del Modelo ---")
    print(f"MAE:  {mae:.4f}")
    print(f"RMSE: {rmse:.4f}")
    print(f"R²:   {r2:.4f}")

    importancia = sorted(zip(feature_cols, model.feature_importances_), key=lambda x: x[1], reverse=True)
    print(f"\nImportancia de Features:")
    for feat, imp in importancia:
        print(f"  {feat}: {imp:.4f}")
    metricas["feature_importance"] = {feat: round(imp, 4) for feat, imp in importancia}

    os.makedirs(os.path.dirname(RUTA_METRICAS), exist_ok=True)
    with open(RUTA_METRICAS, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=2, ensure_ascii=False)

    resultados = df.copy()
    resultados["rating_predicho"] = np.round(y_pred_all, 2)
    resultados["error_prediccion"] = np.abs(resultados["rating"] - resultados["rating_predicho"])
    result_cols = ["restaurante", "reseña", "rating", "rating_predicho", "error_prediccion",
                   "sentimiento", "longitud"]
    resultados[result_cols].to_csv(RUTA_RESULTADOS, index=False, encoding="utf-8")
    print(f"\nResultados guardados en {RUTA_RESULTADOS}")
    print("Regresion completada.")


if __name__ == "__main__":
    main()
