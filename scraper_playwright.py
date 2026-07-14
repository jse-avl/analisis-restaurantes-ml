"""Scraper Playwright: extrae resenas reales de Google Maps para multiples restaurantes.
Genera: data/restaurantes_scraped.csv con formato compatible con el pipeline.

Flujo:
1. Busca "restaurantes en Panama" en Google Maps
2. Obtiene lista de URLs de restaurantes del feed
3. Para cada restaurante, navega a Opiniones y extrae resenas
4. Guarda en CSV
"""
import sys, os, csv, re, json, time
sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf8", buffering=1)

from playwright.sync_api import sync_playwright

RUTA_DATA = os.path.join(os.path.dirname(__file__), "data")

# Queries de busqueda para variety
BUSQUEDAS = [
    "restaurantes en Panama",
    "mejores restaurantes Panama",
    "restaurantes populares Panama ciudad",
    "comida panameña Panama",
    "restaurantes Casco Viejo Panama",
    "restaurantes Obarrio Panama",
]

MAX_RESTAURANTES = 30
MAX_SCROLL_REVIEWS = 30
MAX_REVIEWS_PER_RESTAURANT = 150


def search_restaurants(page, query, max_restaurants=20):
    """Search Google Maps for restaurants, return list of {name, url, rating}."""
    print(f"\nBuscando: '{query}'...")
    try:
        page.goto("https://www.google.com/maps", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
    except:
        pass

    # Search
    try:
        search_box = page.locator("#searchboxinput, input[aria-label*='Buscar'], input[name='q']")
        search_box.wait_for(timeout=10000)
        search_box.click()
        page.wait_for_timeout(300)
        search_box.fill("")
        page.wait_for_timeout(200)
        search_box.fill(query)
        page.wait_for_timeout(300)
        search_box.press("Enter")
        page.wait_for_timeout(5000)
    except Exception as e:
        print(f"  Error en busqueda: {e}")
        return []

    # Scroll feed to load results
    results = []
    seen_urls = set()
    for scroll in range(15):
        try:
            page.evaluate("""
                const feed = document.querySelector('[role=feed]');
                if (feed) feed.scrollTop = feed.scrollHeight;
            """)
            page.wait_for_timeout(1500)

            # Extract restaurant links
            restaurants = page.evaluate("""
                () => {
                    const items = [];
                    document.querySelectorAll('a[href*="/place/"]').forEach(a => {
                        const href = a.getAttribute('href') || '';
                        if (href.includes('/place/') && !href.includes('/place//')) {
                            const name = a.getAttribute('aria-label') || '';
                            if (name && name.length > 2) {
                                items.push({name: name, url: href.startsWith('http') ? href : 'https://www.google.com' + href});
                            }
                        }
                    });
                    return items;
                }
            """)

            for r in restaurants:
                if r["url"] not in seen_urls:
                    seen_urls.add(r["url"])
                    results.append(r)

            print(f"  Scroll {scroll+1}: {len(results)} restaurantes unicos")

            if len(results) >= max_restaurants:
                break
        except Exception as e:
            print(f"  Error scroll {scroll}: {e}")

    return results[:max_restaurants]


def extract_reviews(page, restaurant_url, max_reviews=150):
    """Extract reviews from a restaurant's Google Maps page."""
    reviews_data = []

    try:
        print(f"  Navegando a la pagina...")
        page.goto(restaurant_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(5000)

        # Try second navigation with resolved URL
        resolved = page.url
        if resolved != restaurant_url:
            page.goto(resolved, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(5000)

        # Get restaurant name
        restaurant_name = ""
        try:
            name_el = page.locator(".DUwDvf, h1").first
            restaurant_name = name_el.text_content(timeout=5000) or ""
            restaurant_name = restaurant_name.strip()
        except:
            # Try from title
            title = page.title()
            if " - Google Maps" in title:
                restaurant_name = title.replace(" - Google Maps", "").strip()
            elif "Google Maps" not in title:
                restaurant_name = title.strip()

        print(f"  Restaurante: {restaurant_name}")

        # Click Opiniones tab
        tabs = page.locator("[role='tab']")
        found = False
        for i in range(tabs.count()):
            try:
                text = tabs.nth(i).text_content() or ""
                if "Opinion" in text:
                    tabs.nth(i).click()
                    print(f"  Click en tab '{text}'")
                    page.wait_for_timeout(3000)
                    found = True
                    break
            except:
                continue

        if not found:
            print(f"  No se encontro tab Opiniones")
            # Try alternative selector
            try:
                page.locator("button:has-text('Opiniones')").click(timeout=5000)
                page.wait_for_timeout(3000)
            except:
                pass

        # Scroll to load reviews
        prev_count = 0
        for i in range(MAX_SCROLL_REVIEWS):
            page.evaluate("""
                const panel = document.querySelector('[role=tabpanel]') || 
                             document.querySelector('.m6QErb.DxyBCb') ||
                             document.querySelector('[role=main]');
                if (panel) panel.scrollTop = panel.scrollHeight;
            """)
            page.wait_for_timeout(1500)

            current_count = page.evaluate(
                "document.querySelectorAll('[class*=jft]').length"
            )
            if current_count > prev_count:
                print(f"    Scroll {i+1}: {current_count} cards", end="\r")
                prev_count = current_count
            if current_count >= max_reviews:
                break

        print(f"\n    Total cards: {prev_count}")

        # Extract reviews
        reviews = page.evaluate("""
            (rest_name) => {
                const results = [];
                const cards = document.querySelectorAll('[class*=jft]');
                cards.forEach(card => {
                    let text = '';
                    const textEl = card.querySelector('[class*=MyEned]') || 
                                   card.querySelector('[class*=wiI7pd]') ||
                                   card.querySelector('span[class*="review"]');
                    if (textEl) {
                        text = textEl.textContent.trim();
                    } else {
                        text = card.textContent.trim();
                        // Filter out non-review text (too short or metadata)
                        if (text.length < 20) return;
                        // Remove common non-review patterns
                        if (/^Traducir|^Original|^Más$|^Menos$/.test(text)) return;
                    }

                    if (!text || text.length < 10) return;
                    if (/^Traducir/.test(text)) return;
                    if (text.length > 2000) text = text.substring(0, 2000);

                    let rating = '';
                    const ratingEl = card.querySelector('[aria-label*="estrella"], [aria-label*="star"], [role="img"]');
                    if (ratingEl) {
                        const label = ratingEl.getAttribute('aria-label') || '';
                        const match = label.match(/\\d+/);
                        if (match) rating = match[0];
                    }

                    let reviewer = '';
                    const nameEl = card.querySelector('[class*=d4r55]');
                    if (nameEl) reviewer = nameEl.textContent.trim();

                    let date = '';
                    const dateEl = card.querySelector('[class*=rsqaWe]');
                    if (dateEl) date = dateEl.textContent.trim();

                    results.push({
                        restaurante: rest_name,
                        reseña: text,
                        rating: rating,
                        reviewer: reviewer,
                        fecha: date
                    });
                });
                return results;
            }
        """, restaurant_name)

        print(f"    Extraidas: {len(reviews)} resenas")
        return reviews

    except Exception as e:
        print(f"  Error extrayendo resenas: {e}")
        return []


def save_to_csv(all_reviews, filepath):
    """Save combined reviews to CSV in pipeline format."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    campos = ["restaurante", "categoria", "barrio", "rating", "reseña", "sentimiento", "fecha"]
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for r in all_reviews:
            writer.writerow({
                "restaurante": r.get("restaurante", ""),
                "categoria": r.get("categoria", ""),
                "barrio": r.get("barrio", ""),
                "rating": r.get("rating", ""),
                "reseña": r.get("reseña", ""),
                "sentimiento": r.get("sentimiento", ""),
                "fecha": r.get("fecha", ""),
            })


def main():
    print("=== Scraper Google Maps con Playwright ===\n")

    all_reviews = []
    visited_urls = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(
            locale="es-PA",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        for query in BUSQUEDAS:
            if len(all_reviews) >= 1400:
                break

            restaurants = search_restaurants(page, query, max_restaurants=MAX_RESTAURANTES)
            print(f"  Encontrados: {len(restaurants)}")

            for i, r in enumerate(restaurants):
                if len(all_reviews) >= 1400:
                    break
                if r["url"] in visited_urls:
                    continue
                visited_urls.add(r["url"])

                print(f"\n--- [{len(all_reviews)+1}] Procesando: {r['name']} ---")
                reviews = extract_reviews(
                    page, r["url"],
                    max_reviews=MAX_REVIEWS_PER_RESTAURANT
                )

                if reviews:
                    all_reviews.extend(reviews)
                    print(f"  Total acumulado: {len(all_reviews)} resenas")

        browser.close()

    if all_reviews:
        salida = os.path.join(RUTA_DATA, "reviews_real.csv")
        save_to_csv(all_reviews, salida)
        print(f"\n=== COMPLETADO ===")
        print(f"Total resenas reales extraidas: {len(all_reviews)}")
        print(f"Guardado en: {salida}")

        # Summary by restaurant
        from collections import Counter
        counts = Counter(r["restaurante"] for r in all_reviews)
        print(f"\nResumen por restaurante:")
        for name, count in counts.most_common():
            print(f"  {name}: {count} resenas")
    else:
        print("\nNo se extrajeron resenas.")


if __name__ == "__main__":
    main()
