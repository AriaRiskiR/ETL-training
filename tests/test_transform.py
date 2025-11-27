import pytest
import pandas as pd
import numpy as np # Diperlukan untuk np.nan saat pengujian yang lebih detail
import sys
import os
from datetime import datetime # Untuk perbandingan timestamp jika diperlukan


current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, parent_dir)

from utils.transform import clean_and_transform 

# --- Data Sampel untuk Tes ---
def generate_sample_raw_data_dict():
    """Menghasilkan data mentah sampel untuk pengujian."""
    return {
        "Title": ["Kaos Polos Nyaman", "Celana Jeans Trendi", "Jaket Bomber Kece"],
        "Price": ["$12.50", "$35.00", "$48.75"],
        "Rating": ["⭐ 4.8", "⭐ 4.2", "⭐ 4.5"],
        "Colors": ["2 Colors", "1 Color", "4 Colors"], # Sesuai format input yang diharapkan
        "Size": ["L", "M", "XL"],
        "Gender": ["Unisex", "Male", "Female"],
        "Timestamp": [datetime(2024, 1, 15, 10, 30, 0),
                      datetime(2024, 1, 16, 14, 0, 15),
                      datetime(2024, 1, 17, 18, 45, 30)]
    }

# --- Tes untuk Fungsi clean_and_transform ---

def test_data_transformation_successful_for_valid_inputs():
    """
    Menguji apakah clean_and_transform berhasil memproses DataFrame dengan data valid,
    menghasilkan tipe data yang benar dan nilai yang sesuai.
    """
    raw_data = generate_sample_raw_data_dict()
    input_df = pd.DataFrame(raw_data)
    transformed_df = clean_and_transform(input_df)

    assert not transformed_df.empty, "DataFrame hasil tidak boleh kosong untuk input valid."
    assert len(transformed_df) == 3, "Jumlah baris harus tetap sama untuk input valid ini."

    # Verifikasi tipe data
    assert transformed_df["Rating"].dtype == float, "Tipe data kolom Rating harus float."
    assert transformed_df["Price"].dtype == float, "Tipe data kolom Price harus float."
    assert transformed_df["Colors"].dtype == int, "Tipe data kolom Colors harus int."
    assert pd.api.types.is_string_dtype(transformed_df["Size"]), "Tipe data kolom Size harus string."
    assert pd.api.types.is_string_dtype(transformed_df["Gender"]), "Tipe data kolom Gender harus string."
    assert pd.api.types.is_string_dtype(transformed_df["Timestamp"]), "Tipe data kolom Timestamp harus string setelah format."

    # Verifikasi nilai yang ditransformasi (contoh)
    assert transformed_df["Rating"].iloc[0] == 4.8
    assert transformed_df["Price"].iloc[0] == 12.50 * 16000 # (12.50 * 16000 = 200000.0)
    assert transformed_df["Price"].iloc[1] == 35.00 * 16000 # (35.00 * 16000 = 560000.0)
    assert transformed_df["Colors"].iloc[0] == 2
    assert transformed_df["Colors"].iloc[1] == 1 # "1 Color" akan menghasilkan 1

    # Verifikasi format timestamp (ISO 8601 dengan 'T')
    assert transformed_df["Timestamp"].iloc[0].startswith("2024-01-15T10:30:00."), "Format timestamp tidak sesuai."
    assert "T" in transformed_df["Timestamp"].iloc[1], "Format timestamp harus mengandung 'T'."


def test_transformation_handles_specific_invalid_rating_string():
    """
    Menguji apakah baris dengan string 'Rating Tidak Valid' (sesuai logika transform.py)
    dihapus dari DataFrame.
    """
    data_with_invalid_rating_str = {
        "Title": ["Produk Oke", "Produk Dihapus"],
        "Price": ["$10.00", "$20.00"],
        "Rating": ["⭐ 4.0", "Rating Tidak Valid"], # String spesifik yang difilter
        "Colors": ["3 Colors", "1 Color"],
        "Size": ["M", "S"],
        "Gender": ["Male", "Female"],
        "Timestamp": [datetime(2024, 2, 1), datetime(2024, 2, 2)]
    }
    input_df = pd.DataFrame(data_with_invalid_rating_str)
    transformed_df = clean_and_transform(input_df)

    assert len(transformed_df) == 1, "Baris dengan 'Rating Tidak Valid' seharusnya dihapus."
    assert transformed_df.iloc[0]["Title"] == "Produk Oke", "Produk yang tersisa salah."
    assert "Produk Dihapus" not in transformed_df["Title"].values, "Produk dengan rating tidak valid seharusnya tidak ada."


def test_transformation_handles_unparseable_rating_value():
    """
    Menguji apakah baris dengan nilai Rating yang tidak bisa diparsing (setelah filter awal)
    dihapus karena menjadi NaN dan kemudian di-dropna.
    """
    data_with_unparseable_rating = {
        "Title": ["Produk Gagal Rating"],
        "Price": ["$15.00"],
        "Rating": ["Rating Bintang Lima"], # Tidak sesuai format "⭐ X.X" dan bukan "Rating Tidak Valid"
        "Colors": ["2 Colors"],
        "Size": ["L"],
        "Gender": ["Unisex"],
        "Timestamp": [datetime(2024, 2, 3)]
    }
    input_df = pd.DataFrame(data_with_unparseable_rating)
    transformed_df = clean_and_transform(input_df)

    assert transformed_df.empty, "Baris dengan Rating yang tidak bisa diparsing menjadi angka seharusnya dihapus."

def test_transformation_handles_unconvertible_price_value():
    """
    Menguji apakah baris dengan nilai Price yang tidak bisa dikonversi menjadi numerik
    dihapus dari DataFrame.
    """
    data_with_bad_price = {
        "Title": ["Produk Gagal Harga"],
        "Price": ["Dua Puluh Dolar"], # String yang tidak bisa dikonversi
        "Rating": ["⭐ 3.5"],
        "Colors": ["1 Color"],
        "Size": ["XL"],
        "Gender": ["Male"],
        "Timestamp": [datetime(2024, 2, 4)]
    }
    input_df = pd.DataFrame(data_with_bad_price)
    transformed_df = clean_and_transform(input_df)

    assert transformed_df.empty, "Baris dengan Price yang tidak valid seharusnya dihapus."

def test_transformation_handles_colors_default_for_unparseable_string():
    """
    Menguji bagaimana kolom 'Colors' diproses jika inputnya string yang tidak mengandung angka,
    seharusnya diisi dengan nilai default 1.
    """
    data_with_special_colors = {
        "Title": ["Produk Warna Khusus"],
        "Price": ["$22.00"],
        "Rating": ["⭐ 4.1"],
        "Colors": ["Banyak Pilihan Warna"], # String tanpa angka eksplisit di awal
        "Size": ["S"],
        "Gender": ["Female"],
        "Timestamp": [datetime(2024, 2, 5)]
    }
    input_df = pd.DataFrame(data_with_special_colors)
    transformed_df = clean_and_transform(input_df)

    assert not transformed_df.empty
    assert transformed_df.iloc[0]["Colors"] == 1, "Colors tanpa angka seharusnya diisi default 1."


def test_transformation_process_empty_dataframe():
    """
    Menguji apakah fungsi mengembalikan DataFrame kosong jika inputnya adalah DataFrame kosong.
    """
    empty_df = pd.DataFrame({
        "Title": [], "Price": [], "Rating": [], "Colors": [],
        "Size": [], "Gender": [], "Timestamp": []
    })
    transformed_df = clean_and_transform(empty_df)
    assert transformed_df.empty, "Output harus DataFrame kosong jika inputnya kosong."

def test_transformation_handles_problematic_timestamp_conversion():
    """
    Menguji bagaimana fungsi menangani timestamp yang tidak bisa dikonversi.
    pd.to_datetime(errors='coerce') akan menghasilkan NaT.
    strftime pada NaT dalam Series akan menghasilkan NaN (float) untuk kolom Timestamp.
    """
    data_with_bad_timestamp = {
        "Title": ["Produk Timestamp Aneh"],
        "Price": ["$5.00"],
        "Rating": ["⭐ 3.0"],
        "Colors": ["1 Color"],
        "Size": ["M"],
        "Gender": ["Unisex"],
        "Timestamp": ["BUKAN_TANGGAL_VALID"] # Timestamp yang tidak valid
    }
    input_df = pd.DataFrame(data_with_bad_timestamp)
    transformed_df = clean_and_transform(input_df)

    # DataFrame TIDAK AKAN kosong
    assert not transformed_df.empty, "DataFrame seharusnya tidak kosong."
    assert len(transformed_df) == 1, "Satu baris data seharusnya tetap ada."

    # Kolom Timestamp untuk baris tersebut seharusnya NaN
    # pd.isna() bisa mengecek NaN float maupun pd.NaT (jika strftime tidak dilakukan)
    assert pd.isna(transformed_df.iloc[0]["Timestamp"]), "Kolom Timestamp seharusnya NaN setelah konversi gagal dan strftime."