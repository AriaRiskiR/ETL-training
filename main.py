from datetime import datetime
import sys
import os
from utils.extract import collect_fashion_data
from utils.transform import clean_and_transform
from utils.load import process_data

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)




def main():
    """Fungsi utama untuk menjalankan proses ETL fashion data."""
    try:
        print(f"[{datetime.now()}] [INFO] Memulai proses pengumpulan data...")
        raw_products = collect_fashion_data(pages_to_scrape=50)  

        if raw_products.empty:
            print(f"[{datetime.now()}] [ERROR] Tidak ada data yang berhasil dikumpulkan.")
            return
        
        print(f"[{datetime.now()}] [SUCCESS] Jumlah data awal: {len(raw_products)}")
        
        print(f"[{datetime.now()}] [INFO] Memulai proses pembersihan data...")
        cleaned_df = clean_and_transform(raw_products)
        
        if cleaned_df.empty:
            print(f"[{datetime.now()}] [ERROR] Tidak ada data yang tersisa setelah pembersihan.")
            return
            
        print(f"[{datetime.now()}] [SUCCESS] Data setelah dibersihkan: {len(cleaned_df)} baris")
        
        print(f"[{datetime.now()}] [INFO] Memulai proses penyimpanan data...")
        process_data(df=cleaned_df)
        print(f"[{datetime.now()}] [SUCCESS] Proses ETL selesai")
        
    except Exception as error:
        print(f"[{datetime.now()}] [ERROR] Terjadi kesalahan: {str(error)}")

if __name__ == "__main__":
    main()