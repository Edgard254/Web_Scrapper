import httpx
from selectolax.parser import HTMLParser
import time
from urllib.parse import urljoin
from dataclasses import asdict, dataclass, fields
import json
import csv

@dataclass
class Item:
    name: str | None
    item_num: str | None
    price: str | None
    rating: float | None

def get_html(url, **kwargs):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    if kwargs.get("page"):
        resp = httpx.get(
            url + str(kwargs.get("page")), headers=headers, follow_redirects=True
            )
    else:
        resp = httpx.get(url, headers=headers, follow_redirects=True)

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        print(
            f"Error response {exc.response.status_code} while requesting {exc.request.url!r}. Page Limit Exceeded"
        )
        return False
    html = HTMLParser(resp.text)
    return html

def extract_text(html, sel):
    try:
        text = html.css_first(sel).text()
        return clean_data(text)
    except AttributeError:
        return None
    

def export_to_json(products):
    with open("products.json", "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=4)

def export_to_csv(products):
    field_names = [field.name for field in fields(Item)]
    with open("products.csv", "w") as f:
        writer = csv.DictWriter(f, field_names)
        writer.writeheader()
        writer.writerows(products)
    print("saved to csv")

def append_to_csv(product):
    field_names = [field.name for field in fields(Item)]
    with open("appendcsv.csv", "a") as f:
        writer = csv.DictWriter(f, field_names)
        writer.writerow(product)

def clean_data(value):
    chars_to_remove = ["$", "Item", "#"]
    for char in chars_to_remove:
        if char in value:
            value = value.replace(char, "")
    return value.strip()
    

def parse_search_page(html):
    products = html.css("li.VcGDfKKy_dvNbxUqm29K")
    for product in products:
        yield urljoin("https://www.rei.com", product.css_first("a").attributes["href"]) 

def parse_item_page(html):
    new_item = Item(
        name=extract_text(html, "h1#product-page-title"),
        item_num=extract_text(html, "span#product-item-number"),
        price=extract_text(html, "span#buy-box-product-price"),
        rating=extract_text(html, "span.cdr-rating__number_13-5-3"),
    )
    return asdict(new_item)

def main():
    products = []
    baseurl = "https://www.rei.com/c/camping-and-hiking/f/scd-deals?page="
    for x in range(1, 2):
        print(f"Getting page: {x}") 
        html = get_html(baseurl, page=x)
        if html is False:
            break
        product_urls = parse_search_page(html)
        for url in product_urls:
            print(url)
            html = get_html(url)
            append_to_csv(parse_item_page(html))
            time.sleep(0.1)

    export_to_json(products)
    # export_to_csv(products)

        
if __name__ == "__main__":
    main()
