import pandas as pd

def clean_and_transform(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Membersihkan dan mengubah data produk agar siap untuk proses selanjutnya.

    Args:
        dataframe (pd.DataFrame): Data mentah hasil scraping.

    Returns:
        pd.DataFrame: Data yang sudah dibersihkan dan diubah tipe datanya,
                      atau DataFrame kosong jika terjadi kesalahan.
    """
    try:
        if dataframe.empty:
            print("[Transformasi] DataFrame kosong, tidak ada yang diproses.")
            return pd.DataFrame()
            
        # Buat salinan untuk menghindari SettingWithCopyWarning
        filtered_df = dataframe.copy()
        
        # Buang baris dengan rating yang tidak valid
        filtered_df = filtered_df[filtered_df['Rating'] != 'Rating Tidak Valid']

        # Ekstrak nilai rating sebagai float dari string seperti '⭐ 4.5'
        filtered_df['Rating'] = filtered_df['Rating'].str.extract(r'⭐\s*(\d+(?:\.\d+)?)')
        filtered_df['Rating'] = pd.to_numeric(filtered_df['Rating'], errors='coerce')
        
        # Tangani nilai NaN setelah konversi
        filtered_df = filtered_df.dropna(subset=['Rating'])

        # Bersihkan kolom Price, hapus simbol '$' dan koma, konversi ke float, lalu ke IDR
        filtered_df['Price'] = (
            filtered_df['Price']
            .str.replace('$', '', regex=False)
            .str.replace(',', '', regex=False)
        )
        # Konversi ke float dan kalikan dengan kurs
        filtered_df['Price'] = pd.to_numeric(filtered_df['Price'], errors='coerce') * 16000
        filtered_df['Price'] = filtered_df['Price'].round(2)
        
        # Tangani nilai NaN setelah konversi harga
        filtered_df = filtered_df.dropna(subset=['Price'])

        #Mengubah Colors
        extracted_color_series = filtered_df['Colors'].str.extract(r'(\d+)')[0]
        numeric_color_series = pd.to_numeric(extracted_color_series, errors='coerce')
        filled_color_series = numeric_color_series.fillna(1)
        filtered_df['Colors'] = filled_color_series.astype(int)

        # Pastikan Size dan Gender bertipe string
        filtered_df['Size'] = filtered_df['Size'].astype(str)
        filtered_df['Gender'] = filtered_df['Gender'].astype(str)

        # Format kolom Timestamp ke ISO 8601, abaikan error konversi
        filtered_df['Timestamp'] = pd.to_datetime(filtered_df['Timestamp'], errors='coerce').dt.strftime('%Y-%m-%dT%H:%M:%S.%f')

        return filtered_df

    except Exception as err:
        print(f"[Transformasi Error] Terjadi masalah saat membersihkan data: {err}")
        return pd.DataFrame()