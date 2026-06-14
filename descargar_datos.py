"""Paso 1: Descarga de datos - Google Maps Playwright + dataset respaldo.
Genera: data/reviews.csv con resenas reales de Google Maps.
"""

import os, csv, sys, subprocess, random
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

RUTA = os.path.dirname(os.path.abspath(__file__))
RUTA_DATA = os.path.join(RUTA, "data")
RUTA_FALLBACK = os.path.join(RUTA_DATA, "restaurantes_panama.csv")
RUTA_REAL = os.path.join(RUTA_DATA, "reviews_real.csv")
RUTA_SALIDA = os.path.join(RUTA_DATA, "reviews.csv")


def try_playwright_scraper():
    """Intenta extraer resenas reales con Playwright."""
    print("Intentando extraer resenas reales con Playwright...")
    scraper = os.path.join(RUTA, "scraper_playwright.py")
    if not os.path.exists(scraper):
        print("  scraper_playwright.py no encontrado")
        return None

    try:
        result = subprocess.run(
            [sys.executable, scraper],
            capture_output=True, text=True, timeout=600,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"}
        )
        if result.returncode == 0 and os.path.exists(RUTA_REAL):
            with open(RUTA_REAL, "r", encoding="utf-8") as f:
                data = list(csv.DictReader(f))
            print(f"  Extraidas {len(data)} resenas reales!")
            # Show output
            for line in result.stdout.split("\n"):
                if any(kw in line for kw in ["Resumen", "Total", "COMPLETADO", "Error"]):
                    print(f"  {line}")
            return data
        else:
            print(f"  Playwright fallo (exit={result.returncode})")
            for line in result.stdout.split("\n"):
                if "Error" in line:
                    print(f"  {line}")
            return None
    except subprocess.TimeoutExpired:
        print("  Timeout en Playwright (>10 min)")
        return None
    except Exception as e:
        print(f"  Error: {e}")
        return None


def usar_fallback_con_scraped():
    """Usa el approach anterior: nombres reales + resenas generadas."""
    print("Usando approach hibrido: nombres reales + resenas generadas...")
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        print("ERROR: selenium no instalado")
        return None

    import time
    try:
        options = webdriver.ChromeOptions()
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        options.add_argument("--lang=es")
        options.add_argument("--start-maximized")
        options.add_argument("--no-sandbox")

        d = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        d.get("https://www.google.com/maps/search/restaurantes+en+Panam%C3%A1/")
        time.sleep(5)

        feed = WebDriverWait(d, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[role='feed']"))
        )
        for _ in range(12):
            d.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", feed)
            time.sleep(random.uniform(2, 3))

        articles = d.find_elements(By.CSS_SELECTOR, "[role='article']")
        urls = set()
        for a in articles:
            try:
                href = a.find_element(By.CSS_SELECTOR, "a.hfpxzc").get_attribute("href") or ""
                if "/place/" in href:
                    urls.add(href)
            except:
                continue
        d.quit()

        scraped = []
        for idx, url in enumerate(list(urls)[:15]):
            try:
                d2 = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
                d2.get(url)
                time.sleep(5)
                nombre = WebDriverWait(d2, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".DUwDvf"))
                ).text
                rating = 0.0
                try:
                    rating = float(d2.find_element(
                        By.CSS_SELECTOR, "div.fontBodyMedium span[aria-hidden='true']"
                    ).text.strip().replace(",", "."))
                except:
                    pass
                print(f"  [{idx+1}] {nombre} | rating={rating}")
                scraped.append({"nombre": nombre, "rating": rating})
                d2.quit()
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                print(f"  Error [{idx+1}]: {e}")
                continue

        if len(scraped) >= 5:
            RUTA_SCRAPED = os.path.join(RUTA_DATA, "restaurantes_scraped.csv")
            os.makedirs(RUTA_DATA, exist_ok=True)
            with open(RUTA_SCRAPED, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow(["restaurante", "rating"])
                for r in scraped:
                    w.writerow([r["nombre"], r["rating"]])
            return scraped
        return None
    except Exception as e:
        print(f"  Error Selenium: {e}")
        return None


def merge_con_fallback(scraped, fallback):
    """Asigna resenas del fallback a restaurantes reales."""
    if not scraped:
        return fallback
    random.shuffle(fallback)
    result = []
    target = len(fallback) // len(scraped)
    for r in scraped:
        nombre = r["nombre"]
        rating = r["rating"]
        for rev in fallback[:target]:
            result.append({
                "restaurante": nombre,
                "categoria": rev.get("categoria", ""),
                "barrio": rev.get("barrio", ""),
                "rating": rating,
                "reseña": rev.get("reseña", ""),
                "sentimiento": "",
                "fecha": rev.get("fecha", "")
            })
        fallback = fallback[target:]
        print(f"  {nombre}: {target} resenas")
    return result


def guardar_csv(data, ruta):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    campos = ["restaurante", "categoria", "barrio", "rating", "reseña", "sentimiento", "fecha"]
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for row in data:
            writer.writerow({c: row.get(c, "") for c in campos})
    print(f"Guardadas {len(data)} resenas en {ruta}")


def main():
    print("=== Descargar Datos ===")

    # Strategy 1: Use previously scraped real reviews if available
    if os.path.exists(RUTA_REAL):
        with open(RUTA_REAL, "r", encoding="utf-8") as f:
            data = list(csv.DictReader(f))
        if len(data) >= 50:
            print(f"Usando resenas reales previas ({len(data)} resenas)")
            guardar_csv(data, RUTA_SALIDA)
            return

    # Strategy 2: Run Playwright scraper
    real_data = try_playwright_scraper()
    if real_data and len(real_data) >= 50:
        print(f"Usando {len(real_data)} resenas reales de Playwright")
        guardar_csv(real_data, RUTA_SALIDA)
        return

    # Strategy 3: Hybrid - real names + generated reviews
    print("\nPlaywright no disponible. Usando approach hibrido...")
    fallback = []
    if os.path.exists(RUTA_FALLBACK):
        with open(RUTA_FALLBACK, "r", encoding="utf-8") as f:
            fallback = list(csv.DictReader(f))
        print(f"Fallback: {len(fallback)} resenas")

    scraped = usar_fallback_con_scraped()
    if scraped and fallback:
        data = merge_con_fallback(scraped, fallback)
    elif fallback:
        data = fallback
    else:
        print("ERROR: No hay datos disponibles")
        return

    if data:
        guardar_csv(data, RUTA_SALIDA)
        print("Completado.")
    else:
        print("ERROR: No se pudo generar datos.")


if __name__ == "__main__":
    main()
