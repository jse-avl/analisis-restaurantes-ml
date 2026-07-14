"""Ejecuta el pipeline completo de análisis de reseñas de restaurantes."""

import subprocess
import sys
import os

RUTA = os.path.dirname(os.path.abspath(__file__))
PIPELINE = [
    ("descargar_datos.py", "Descargando datos..."),
    ("limpiar_datos.py", "Limpiando datos..."),
    ("analizar_sentimiento.py", "Analizando sentimiento..."),
    ("clustering.py", "Generando clusters..."),
    ("regresion.py", "Entrenando modelo de regresion Random Forest..."),
    ("exportar_powerbi.py", "Exportando esquema estrella para Power BI..."),
]


def main():
    os.chdir(RUTA)
    print("=" * 60)
    print("  PIPELINE - Analisis de Resenas de Restaurantes")
    print("  Grupo 5: Christian Duraty, Yireikis Abrego,")
    print("           Jorge Izarra, Jose Avila")
    print("=" * 60)

    for script, msg in PIPELINE:
        print(f"\n{'=' * 40}")
        print(f"  Paso: {msg}")
        print(f"  Script: {script}")
        print(f"{'=' * 40}\n")

        result = subprocess.run(
            [sys.executable, os.path.join(RUTA, script)],
            capture_output=False,
            text=True,
        )

        if result.returncode != 0:
            print(f"\n  ERROR en {script}")
            print(f"  Salida: {result.stderr}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETADO EXITOSAMENTE")
    print("=" * 60)
    print("\n  Para iniciar el dashboard:")
    print(f"  streamlit run app.py")
    print("\n  O directamente:")
    print(f"  python -m streamlit run app.py")


if __name__ == "__main__":
    main()
