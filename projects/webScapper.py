import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def clean_text(text):
    return " ".join(text.split()) if text else None


def extract_price(result):
    price_box = result.select_one("span.a-price")
    if price_box:
        offscreen = price_box.select_one("span.a-offscreen")
        if offscreen:
            return clean_text(offscreen.get_text())
        return clean_text(price_box.get_text())
    return None


def extract_review(result):
    for selector in [
        "span.a-icon-alt",
        "span.a-size-base",
        "span.a-size-small",
        "span[aria-label*='stars']",
        "span[aria-label*='ratings']",
    ]:
        elem = result.select_one(selector)
        if elem:
            text = clean_text(elem.get_text(" ", strip=True))
            if text and ("out of 5" in text or "rating" in text.lower() or "review" in text.lower()):
                return text

    for elem in result.find_all("span"):
        text = clean_text(elem.get_text(" ", strip=True))
        if text and ("out of 5" in text or "rating" in text.lower() or "review" in text.lower()):
            return text

    return None


def scrape_amazon_in(query="monitor", limit=10):
    url = f"https://www.amazon.in/s?k={quote(query)}"
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.select("div[data-component-type='s-search-result']")

    products = []
    for item in results[:limit]:
        title_elem = item.select_one("h2 a span") or item.select_one("h2 span")
        title = clean_text(title_elem.get_text(" ", strip=True)) if title_elem else None
        if not title:
            continue

        products.append(
            {
                "title": title,
                "price": extract_price(item),
                "review": extract_review(item),
            }
        )

    return products


if __name__ == "__main__":
    products = scrape_amazon_in("monitor", limit=10)
    for product in products:
        print(f"Title: {product['title']}")
        print(f"Price: {product['price']}")
        print(f"Review: {product['review']}")
        print("-" * 40)
