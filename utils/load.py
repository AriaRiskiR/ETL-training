import pandas as pd
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

class DataSaver:
    """Kelas untuk menyimpan DataFrame ke berbagai penyimpanan."""

    def __init__(self, df: pd.DataFrame):
        """Inisialisasi dengan DataFrame yang akan disimpan.
        
        Args:
            df (pd.DataFrame): DataFrame yang akan disimpan ke berbagai penyimpanan
        """
        self.df = df

    def save_as_csv(self, filename: str = 'products.csv'):
        """Menyimpan DataFrame ke file CSV.
        
        Args:
            filename (str): Nama file CSV yang akan dibuat
        """
        try:
            if self.df.empty:
                print(f"[CSV] DataFrame kosong, tidak ada yang disimpan.")
                return
                
            self.df.to_csv(filename, index=False)
            print(f"[CSV] Data berhasil disimpan ke {filename}")
        except Exception as e:
            print(f"[CSV Error] {e}")

    def save_to_google_sheets(self, spreadsheet_info: dict, credential_file: str = 'google-sheets-api.json'):
        """Menyimpan DataFrame ke Google Spreadsheet.
        
        Args:
            spreadsheet_info (dict): Informasi spreadsheet, harus berisi 'spreadsheet_id' dan 'range_name'
            credential_file (str): Path ke file kredensial Google Service Account
        """
        try:
            if self.df.empty:
                print(f"[Google Sheets] DataFrame kosong, tidak ada yang disimpan.")
                return
                
            creds = Credentials.from_service_account_file(
                credential_file,
                scopes=["https://www.googleapis.com/auth/spreadsheets"]
            )
            service = build('sheets', 'v4', credentials=creds)

            # Menghapus data lama
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_info['spreadsheet_id'],
                range=spreadsheet_info['range_name'],
            ).execute()

            # Format data
            values = [self.df.columns.tolist()] + self.df.values.tolist()
            body = {'values': values}

            # Menyimpan data
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_info['spreadsheet_id'],
                range=spreadsheet_info['range_name'],
                valueInputOption="RAW",
                body=body
            ).execute()

            print(f"[Google Sheets] Data berhasil disimpan ke {spreadsheet_info['range_name']}.")
        except Exception as e:
            print(f"[Google Sheets Error] {e}")

def process_data(df: pd.DataFrame):
    """Memproses dan menyimpan data ke berbagai penyimpanan.
    
    Args:
        df (pd.DataFrame): DataFrame yang sudah dibersihkan dan disiapkan
    """
    data_saver = DataSaver(df)

    # Konfigurasi database dan Google Sheets
    spreadsheet_info = {
        'spreadsheet_id': '1jo5MFyc1SXzgAeFqR9QLKlHIyPexXeh3LCbKrKW_hdI', 
        'range_name': 'Sheet1!A1'
    }

    # Simpan data ke berbagai sumber
    data_saver.save_as_csv()
    data_saver.save_to_google_sheets(spreadsheet_info)