import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import requests # Diperlukan untuk requests.exceptions.RequestException

# Menambahkan direktori parent ke sys.path agar modul utils bisa diimpor
current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(parent_dir)

# Impor fungsi-fungsi yang akan diuji dari modul utils.extract
from utils.extract import (
    retrieve_page_content,
    parse_text_by_keyword,
    parse_fashion_item,
    collect_fashion_data,
    HEADERS
)

class TestDataExtractionLogic(unittest.TestCase):
    """Kumpulan tes untuk memverifikasi fungsionalitas modul ekstraksi data."""

    @patch('utils.extract.requests.get')
    def test_retrieve_page_html_on_success(self, mock_http_get):
        """Tes: retrieve_page_content mengembalikan konten HTML jika request sukses (status 200)."""
        # Persiapan mock untuk respons HTTP yang sukses
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Konten Uji Coba</body></html>"
        mock_response.raise_for_status = MagicMock() # Tidak ada error yang di-raise
        mock_http_get.return_value = mock_response

        test_url = "http://contoh.com/sukses"
        # Panggil fungsi yang diuji
        html_text = retrieve_page_content(test_url)

        # Verifikasi: Konten yang diterima sesuai dan request.get dipanggil dengan benar
        self.assertEqual(html_text, "<html><body>Konten Uji Coba</body></html>")
        self.assertEqual(mock_http_get.call_count, 1) # Pastikan dipanggil sekali
        mock_http_get.assert_called_once_with(test_url, headers=HEADERS, timeout=10)

    @patch('utils.extract.requests.get')
    def test_retrieve_page_html_on_request_exception(self, mock_http_get):
        """Tes: retrieve_page_content mengembalikan None jika terjadi RequestException (misal: jaringan error)."""
        # Persiapan mock untuk mensimulasikan kegagalan request
        mock_http_get.side_effect = requests.exceptions.RequestException("Simulasi Error Jaringan")

        test_url = "http://contoh.com/gagal"
        # Panggil fungsi yang diuji
        html_text = retrieve_page_content(test_url)

        # Verifikasi: Hasilnya None dan request.get tetap dipanggil
        self.assertIsNone(html_text)
        self.assertEqual(mock_http_get.call_count, 1)
        mock_http_get.assert_called_once_with(test_url, headers=HEADERS, timeout=10)

    def test_parse_keyword_text_when_found(self):
        """Tes: parse_text_by_keyword berhasil mengekstrak teks yang diinginkan jika keyword dan pola cocok."""
        # Persiapan mock elemen-elemen HTML (sebagai objek BeautifulSoup tag)
        mock_p_rating = MagicMock()
        mock_p_rating.get_text.return_value = "Rating: ⭐ 4.5 Bintang" # Teks yang akan diproses
        mock_p_colors = MagicMock()
        mock_p_colors.get_text.return_value = "Colors: 3 pilihan warna"

        html_elements = [mock_p_rating, mock_p_colors]
        target_keyword = "Rating"
        extraction_pattern = r"Rating:\s*(⭐\s*\d+(?:\.\d+)?)" # Pola untuk mengekstrak rating

        # Panggil fungsi yang diuji
        extracted_info = parse_text_by_keyword(html_elements, target_keyword, extraction_pattern)

        # Verifikasi: Teks yang diekstrak sesuai dengan pola
        self.assertEqual(extracted_info, "⭐ 4.5")

    def test_parse_keyword_text_uses_default_fallback_if_keyword_missing(self):
        """Tes: parse_text_by_keyword mengembalikan fallback default ("Tidak Diketahui") jika keyword tidak ditemukan dalam elemen."""
        mock_p_colors = MagicMock()
        mock_p_colors.get_text.return_value = "Warna: Merah"
        mock_p_size = MagicMock()
        mock_p_size.get_text.return_value = "Ukuran: M"

        html_elements = [mock_p_colors, mock_p_size]
        target_keyword = "Rating" # Keyword ini tidak ada
        extraction_pattern = r"Rating:\s*(⭐\s*\d+(?:\.\d+)?)"

        # Panggil fungsi; fallback default ("Tidak Diketahui") akan digunakan
        extracted_info = parse_text_by_keyword(html_elements, target_keyword, extraction_pattern)
        # Verifikasi: Hasilnya adalah fallback default
        self.assertEqual(extracted_info, "Tidak Diketahui")

    def test_parse_keyword_text_uses_default_fallback_if_pattern_unmatched(self):
        """Tes: parse_text_by_keyword mengembalikan fallback default ("Tidak Diketahui") jika keyword ditemukan tapi pola regex tidak cocok."""
        mock_p_rating_bad_format = MagicMock()
        mock_p_rating_bad_format.get_text.return_value = "Rating adalah Baik" # Keyword ada, tapi formatnya salah

        html_elements = [mock_p_rating_bad_format]
        target_keyword = "Rating"
        extraction_pattern = r"Rating:\s*(⭐\s*\d+(?:\.\d+)?)" # Pola mengharapkan format bintang

        extracted_info = parse_text_by_keyword(html_elements, target_keyword, extraction_pattern)
        # Verifikasi: Hasilnya adalah fallback default
        self.assertEqual(extracted_info, "Tidak Diketahui")

    def test_parse_keyword_text_uses_provided_fallback(self):
        """Tes: parse_text_by_keyword menggunakan nilai fallback kustom yang diberikan saat pencarian gagal."""
        mock_p_info = MagicMock()
        mock_p_info.get_text.return_value = "Info acak lainnya"

        html_elements = [mock_p_info]
        target_keyword = "Material" # Keyword tidak ada
        extraction_pattern = r"Material:\s*(.*)"
        custom_fallback = "Material Tidak Tersedia" # Fallback kustom

        # Panggil fungsi dengan fallback kustom
        extracted_info = parse_text_by_keyword(html_elements, target_keyword, extraction_pattern, custom_fallback)
        # Verifikasi: Hasilnya adalah fallback kustom
        self.assertEqual(extracted_info, custom_fallback)

    def test_parse_one_item_details_successful_extraction(self):
        """Tes: parse_fashion_item berhasil mengekstrak semua detail produk dari kartu HTML."""
        # Contoh konten HTML untuk satu kartu produk
        html_source = """
            <div class="collection-card">
                <h3 class="product-title">Produk Contoh Hebat</h3>
                <div class="price-container">$42.99</div>
                <p>Rating: ⭐ 4.9</p>
                <p>Colors: 4 Colors</p>
                <p>Size: XL</p>
                <p>Gender: Unisex</p>
            </div>
        """
        parsed_soup = BeautifulSoup(html_source, 'html.parser')
        item_card = parsed_soup.find('div', class_='collection-card') # Dapatkan elemen kartu

        fixed_dt = datetime(2024, 5, 25, 10, 30, 0) # Timestamp tetap untuk konsistensi tes
        # Patch modul datetime yang digunakan di dalam utils.extract
        with patch('utils.extract.datetime') as mock_dt:
            mock_dt.now.return_value = fixed_dt # Set nilai kembali untuk datetime.now()
            # Panggil fungsi yang diuji
            item_info = parse_fashion_item(item_card)

        # Verifikasi: Pastikan item_info tidak None dan setiap field diekstrak dengan benar
        self.assertIsNotNone(item_info, "Hasil parsing item seharusnya tidak None.")
        self.assertEqual(item_info['Title'], "Produk Contoh Hebat")
        self.assertEqual(item_info['Price'], "$42.99")
        self.assertEqual(item_info['Rating'], "⭐ 4.9")
        self.assertEqual(item_info['Colors'], "4") # Hanya angka yang diekstrak
        self.assertEqual(item_info['Size'], "XL")
        self.assertEqual(item_info['Gender'], "Unisex")
        self.assertEqual(item_info['Timestamp'], fixed_dt)

    def test_parse_one_item_details_when_elements_are_missing(self):
        """Tes: parse_fashion_item menangani kasus di mana beberapa elemen data produk hilang dan menggunakan nilai fallback yang benar."""
        html_source_incomplete = """
            <div class="collection-card">
                <h3 class="product-title">Produk Lain</h3>
                </div>
        """
        parsed_soup = BeautifulSoup(html_source_incomplete, 'html.parser')
        item_card = parsed_soup.find('div', class_='collection-card')

        fixed_dt = datetime(2024, 5, 25, 11, 0, 0)
        with patch('utils.extract.datetime') as mock_dt:
            mock_dt.now.return_value = fixed_dt
            item_info = parse_fashion_item(item_card)

        # Verifikasi: Pastikan item_info tidak None dan nilai fallback digunakan untuk field yang hilang
        self.assertIsNotNone(item_info)
        self.assertEqual(item_info['Title'], "Produk Lain")
        self.assertEqual(item_info['Price'], "Harga Tidak Ada")
        self.assertEqual(item_info['Rating'], "Rating Tidak Valid")
        self.assertEqual(item_info['Colors'], "Warna Tidak Ada")
        self.assertEqual(item_info['Size'], "Ukuran Tidak Diketahui")
        self.assertEqual(item_info['Gender'], "Gender Tidak Diketahui")
        self.assertEqual(item_info['Timestamp'], fixed_dt)

    def test_parse_one_item_details_for_present_but_empty_title(self):
        """Tes: parse_fashion_item menangani kasus di mana tag judul produk ada, tetapi konten teksnya kosong."""
        html_source_empty_title = """
            <div class="collection-card">
                <h3 class="product-title"></h3> <div class="price-container">$30.50</div>
                <p>Rating: ⭐ 3.0</p>
            </div>
        """
        parsed_soup = BeautifulSoup(html_source_empty_title, 'html.parser')
        item_card = parsed_soup.find('div', class_='collection-card')
        item_info = parse_fashion_item(item_card)

        # Verifikasi: Judul akan menjadi string kosong, bukan "Judul Tidak Ditemukan"
        self.assertIsNotNone(item_info)
        self.assertEqual(item_info['Title'], "")
        self.assertEqual(item_info['Price'], "$30.50")
        self.assertEqual(item_info['Rating'], "⭐ 3.0")

    @patch('utils.extract.retrieve_page_content') # Mock fungsi yang dipanggil secara internal
    @patch('utils.extract.parse_fashion_item')    # Mock fungsi yang dipanggil secara internal
    @patch('utils.extract.time.sleep')            # Mock time.sleep
    def test_collect_all_products_from_pages_mocked_success(self, mock_time_sleep, mock_parser_func, mock_fetcher_func):
        """Tes: collect_fashion_data berhasil melakukan scraping (dengan mock) dari satu halaman dan mengembalikan DataFrame."""
        # Persiapan mock untuk retrieve_page_content
        mock_fetcher_func.return_value = """
            <html><body>
                <div class="collection-card">Card1</div>
                <div class="collection-card">Card2</div>
            </body></html>
        """
        # Persiapan mock untuk objek BeautifulSoup dan find_all
        mock_bs_object = MagicMock()
        mock_bs_object.find_all.return_value = [MagicMock(), MagicMock()] # Dua kartu ditemukan

        # Persiapan mock untuk hasil dari parse_fashion_item
        mock_item_data_list = [
            {"Title": "Barang A Mock", "Price": "$15"},
            {"Title": "Barang B Mock", "Price": "$25"}
        ]
        mock_parser_func.side_effect = mock_item_data_list # parse_fashion_item akan mengembalikan ini secara berurutan

        # Patch konstruktor BeautifulSoup yang diimpor di utils.extract
        with patch('utils.extract.BeautifulSoup', return_value=mock_bs_object) as mock_bs_constructor:
            # Panggil fungsi yang diuji
            result_df = collect_fashion_data(pages_to_scrape=1, wait_seconds=0.01)

            # Verifikasi: Hasilnya adalah DataFrame dengan data yang benar
            self.assertIsInstance(result_df, pd.DataFrame)
            self.assertEqual(len(result_df), 2)
            self.assertEqual(result_df.iloc[0]['Title'], "Barang A Mock")
            self.assertEqual(result_df.iloc[1]['Price'], "$25")

            # Verifikasi: Mock dipanggil dengan benar
            mock_fetcher_func.assert_called_once_with('https://fashion-studio.dicoding.dev/')
            mock_bs_constructor.assert_called_once_with(mock_fetcher_func.return_value, "html.parser")
            mock_bs_object.find_all.assert_called_once_with('div', class_='collection-card')
            self.assertEqual(mock_parser_func.call_count, 2)
            mock_time_sleep.assert_called_once_with(0.01)

if __name__ == '__main__':
    unittest.main(verbosity=2) # Menjalankan tes dengan output yang lebih detail