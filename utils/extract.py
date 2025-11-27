import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from datetime import datetime
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
    )
}

def retrieve_page_content(link: str):
    """Mengambil konten HTML dari URL dengan penanganan error jaringan."""
    try:
        resp = requests.get(link, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.RequestException as err:
        print(f"Kesalahan saat mengakses {link}: {err}")
        return None

def parse_text_by_keyword(elements, key, regex_pattern, fallback="Tidak Diketahui"):
    """Cari teks yang mengandung kata kunci dan ekstrak dengan regex yang diberikan."""
    for elem in elements:
        text = elem.get_text(strip=True)
        if key in text:
            found = re.search(regex_pattern, text)
            if found:
                return found.group(1).strip()
    return fallback

def parse_fashion_item(card_div):
    """Ekstrak data produk dari elemen kartu produk."""
    try:
        # Judul produk
        title_tag = card_div.select_one('h3.product-title')
        product_name = title_tag.get_text(strip=True) if title_tag else "Judul Tidak Ditemukan"

        # Harga produk
        price_tag = card_div.find('div', class_='price-container')
        product_price = price_tag.get_text(strip=True) if price_tag else "Harga Tidak Ada"

        # Ambil semua paragraf info
        paragraphs = card_div.find_all('p')

        # Ekstraksi rating, warna, ukuran, dan gender dengan pola berbeda
        rating_val = parse_text_by_keyword(paragraphs, "Rating", r"Rating:\s*(⭐\s*\d+(?:\.\d+)?)", "Rating Tidak Valid")
        color_count = parse_text_by_keyword(paragraphs, "Colors", r"(\d+)\s*Colors", "Warna Tidak Ada")
        size_info = parse_text_by_keyword(paragraphs, "Size", r"Size:\s*(\w+)", "Ukuran Tidak Diketahui")
        gender_info = parse_text_by_keyword(paragraphs, "Gender", r"Gender:\s*(\w+)", "Gender Tidak Diketahui")

        scrape_time = datetime.now()

        return {
            "Title": product_name,
            "Price": product_price,
            "Rating": rating_val,
            "Colors": color_count,
            "Size": size_info,
            "Gender": gender_info,
            "Timestamp": scrape_time
        }
    except Exception as e:
        print(f"Error saat parsing produk: {e}")
        return None

def collect_fashion_data(pages_to_scrape, wait_seconds=2):
    """Kumpulkan data produk fashion dari beberapa halaman dengan delay dan error handling."""
    collected = []
    base_url = "https://fashion-studio.dicoding.dev/"
    for page in range(1, pages_to_scrape + 1):
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}page{page}"

        print(f"Mengambil data dari: {url}")
        html_content = retrieve_page_content(url)
        if not html_content:
            print(f"Gagal mengambil halaman {page}, menghentikan proses.")
            break

        try:
            soup = BeautifulSoup(html_content, "html.parser")
            product_cards = soup.find_all('div', class_='collection-card')
            if not product_cards:
                print(f"Tidak ditemukan produk di halaman {page}.")
                continue

            for card in product_cards:
                item = parse_fashion_item(card)
                if item:
                    collected.append(item)

            time.sleep(wait_seconds)
        except Exception as parse_err:
            print(f"Kesalahan parsing halaman {page}: {parse_err}")
            continue

    return pd.DataFrame(collected) if collected else pd.DataFrame()