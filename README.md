# Plataforma de Análisis de Reseñas de Restaurantes — Panamá

Dashboard interactivo + pipeline ETL que extrae reseñas reales de Google Maps, analiza su sentimiento por aspecto (comida, servicio, precio) usando LLM, y agrupa restaurantes por desempeño mediante clustering no supervisado.

**Grupo 5:** Christian Duraty, Yireikis Abrego, Jorge Izarra, Jose Avila

---

## Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| Scraping | Playwright (Chromium headless) + Selenium (fallback) |
| Procesamiento | Python 3.13 + Pandas, NumPy |
| Sentimiento | LLM (Claude/OpenAI) con respaldo keyword-based |
| Clustering | Scikit-learn (KMeans + StandardScaler) |
| Dashboard | Streamlit + Matplotlib |

## Requisitos del Proyecto (Parcial 2)

| Requisito | Estado |
|-----------|--------|
| Dataset de reseñas (scraping + API) | ✅ Scraping con Playwright + dataset de respaldo |
| Análisis de sentimiento por aspecto con LLM | ✅ Claude/OpenAI extrae sentimiento de comida, servicio y precio |
| Clustering de restaurantes | ✅ KMeans con 4 clusters (rating, popularidad, % positivo) |
| Dashboard comparativo | ✅ 4 pestañas interactivas en Streamlit |
| Sistema de recomendación | ✅ Scoring personalizado con filtros |

## Arquitectura del Pipeline

El pipeline integra **2 fuentes de datos** diferentes:

1. **Google Maps (Playwright)** — Scraping en vivo de reseñas reales
2. **Dataset de respaldo** — CSV con reseñas generadas (fallback cuando no hay scraping)

```
Google Maps (scraping) ──┐
                          ├──→ descargar_datos.py → limpiar_datos.py
Dataset respaldo ────────┘
                                        ↓
                              analizar_sentimiento.py (LLM por aspecto)
                                        ↓
                                    clustering.py
                                        ↓
                                   app.py (Streamlit)
```

### Flujo detallado

| Paso | Script | Descripción | Salida |
|------|--------|-------------|--------|
| 0 | `scraper_playwright.py` | Extrae reseñas reales de Google Maps vía Playwright | `data/reviews_real.csv` |
| 1 | `descargar_datos.py` | Usa reseñas reales o fallback híbrido (Selenium + CSV) | `data/reviews.csv` |
| 2 | `limpiar_datos.py` | Limpieza, deduplicación, clasificación por rating | `data/reviews_clean.csv` |
| 3 | `analizar_sentimiento.py` | Análisis de sentimiento por aspecto con LLM (Claude/OpenAI) o keyword | `data/reviews_con_sentimiento.csv` |
| 4 | `clustering.py` | KMeans sobre rating, popularidad y % positivo | `data/clusters.csv` |
| 5 | `app.py` | Dashboard Streamlit con 4 pestañas | — |

## Origen de los Datos

Las reseñas se extraen de **Google Maps** usando **Playwright** con Chromium en modo headless. El scraper:

1. Busca `"restaurantes en Panama"` en Google Maps
2. Obtiene las URLs de los restaurantes del feed de resultados
3. Navega a la pestaña **Opiniones** de cada restaurante
4. Hace scroll para cargar reseñas vía lazy-loading
5. Extrae: texto, rating, reseñador y fecha

**Dataset actual:** 444 reseñas reales de 5 restaurantes panameños.

## Instalación

```bash
pip install -r requirements.txt
playwright install chromium
```

## Ejecución

### Pipeline completo
```bash
python run_pipeline.py
```

### Dashboard
```bash
python -m streamlit run app.py
```

### Solo scraping (para refrescar datos)
```bash
python scraper_playwright.py
```

## Estructura del Proyecto

```
├── scraper_playwright.py      # Extracción con Playwright
├── descargar_datos.py          # Paso 1: descarga/merge (2 fuentes)
├── limpiar_datos.py            # Paso 2: limpieza y transformación
├── analizar_sentimiento.py     # Paso 3: sentimiento por aspecto (LLM + keyword)
├── clustering.py               # Paso 4: clustering KMeans
├── app.py                      # Dashboard Streamlit
├── run_pipeline.py             # Orquestador del pipeline
├── requirements.txt            # Dependencias
├── .env                        # API keys (ANTHROPIC/OPENAI)
└── data/
    ├── reviews_real.csv        # Reseñas reales (salida del scraper)
    ├── reviews.csv             # Reseñas procesadas (paso 1)
    ├── reviews_clean.csv       # Reseñas limpias (paso 2)
    ├── reviews_con_sentimiento.csv  # Con análisis de sentimiento (paso 3)
    ├── clusters.csv            # Clusters de restaurantes (paso 4)
    └── restaurantes_panama.csv # Dataset de respaldo (2da fuente)
```

## Dashboard — 4 Pestañas

1. **Resumen General** — Métricas globales, distribución de ratings, tabla de restaurantes con filtros por nombre y rating
2. **Análisis por Restaurante** — Rating, sentimiento general, desglose por aspecto (comida/servicio/precio), palabras clave por aspecto, últimas reseñas
3. **Clustering** — Gráfico de dispersión (rating vs % positivo), tablas por cluster, estadísticas agregadas
4. **Recomendaciones** — Top 5 restaurantes según scoring personalizado (rating + sentimiento + popularidad)

## Análisis de Sentimiento por Aspecto

El análisis extrae el sentimiento para **3 aspectos** específicos:

- **Comida** — calidad, sabor, frescura, presentación
- **Servicio** — atención, rapidez, amabilidad del personal
- **Precio** — relación calidad-precio, costo

### Modalidad LLM (recomendada)
Con `ANTHROPIC_API_KEY` o `OPENAI_API_KEY` configurada en `.env`, usa Claude o GPT-4o-mini para extraer sentimiento por aspecto con alta precisión.

### Modalidad keyword (fallback)
Usa listas léxicas en español (+50 términos por aspecto) cuando no hay API key disponible.

## Clustering

Los restaurantes se agrupan en 4 clusters usando **KMeans** con 3 features normalizadas vía `StandardScaler`:

- **Rating promedio** (peso 0.4)
- **% de reseñas positivas** (peso 0.6)
- **Número de reseñas** (popularidad, peso 0.2)

Las etiquetas se asignan ordenando los centroides por calidad: **Excelente → Bueno → Regular → Malo**.

## Sistema de Recomendación

Genera recomendaciones personalizadas basadas en:
- Rating mínimo ajustable
- Preferencia de sentimiento (positivo/neutral)
- Scoring ponderado: 50% rating + 30% sentimiento + 20% popularidad

## Configuración

Copia `.env.example` a `.env` y configura al menos una API key:

```env
ANTHROPIC_API_KEY=tu_clave_aqui
# OPENAI_API_KEY=tu_clave_aqui
```
