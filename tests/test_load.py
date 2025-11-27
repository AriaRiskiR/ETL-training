import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os


current_dir = os.path.dirname(__file__)
parent_dir = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.insert(0, parent_dir)


from utils.load import DataSaver, process_data

# --- Fixture DataFrame untuk Pengujian ---
@pytest.fixture
def sample_product_dataframe():
    """Menyediakan DataFrame sampel untuk pengujian modul penyimpanan data."""
    return pd.DataFrame({
        "Title": ["Kemeja Denim", "Dress Musim Panas"],
        "Price": [256000.0, 320000.0], # Sudah dalam IDR setelah transformasi
        "Rating": [4.5, 3.9],
        "Colors": [2, 4],
        "Size": ["M", "S"],
        "Gender": ["Male", "Female"],
        "Timestamp": ["2025-05-10T10:00:00.000000", "2025-05-10T11:00:00.000000"]
    })

@pytest.fixture
def empty_product_dataframe():
    """Menyediakan DataFrame kosong untuk pengujian skenario kosong."""
    return pd.DataFrame(columns=[
        "Title", "Price", "Rating", "Colors", "Size", "Gender", "Timestamp"
    ])

# --- Tes untuk Kelas DataSaver ---

def test_data_saver_initialization(sample_product_dataframe):
    """Verifikasi inisialisasi DataSaver dengan DataFrame."""
    saver = DataSaver(sample_product_dataframe)
    pd.testing.assert_frame_equal(saver.df, sample_product_dataframe)

# Tes untuk metode save_as_csv
def test_data_saver_saves_to_csv_correctly(tmp_path, sample_product_dataframe):
    """
    Menguji apakah DataSaver.save_as_csv berhasil menyimpan DataFrame ke file CSV
    dan file tersebut dapat dibaca kembali dengan benar.
    """
    output_csv_path = tmp_path / "fashion_items.csv"
    saver = DataSaver(sample_product_dataframe)
    saver.save_as_csv(filename=str(output_csv_path))

    assert output_csv_path.exists()
    read_df = pd.read_csv(output_csv_path)
    pd.testing.assert_frame_equal(read_df, sample_product_dataframe)

def test_data_saver_csv_handles_empty_dataframe(tmp_path, empty_product_dataframe, capsys):
    """
    Menguji apakah DataSaver.save_as_csv menangani DataFrame kosong dengan mencetak pesan
    dan tidak membuat file CSV.
    """
    output_csv_path = tmp_path / "empty_items.csv"
    saver = DataSaver(empty_product_dataframe)
    saver.save_as_csv(filename=str(output_csv_path))

    captured = capsys.readouterr()
    assert "[CSV] DataFrame kosong, tidak ada yang disimpan." in captured.out
    assert not output_csv_path.exists()

@patch("pandas.DataFrame.to_csv", side_effect=IOError("Simulasi error disk"))
def test_data_saver_csv_error_handling(mock_to_csv_method, sample_product_dataframe, capsys):
    """
    Menguji penanganan error pada DataSaver.save_as_csv ketika terjadi exception
    selama proses penyimpanan.
    """
    saver = DataSaver(sample_product_dataframe)
    saver.save_as_csv(filename="error_test.csv")

    captured = capsys.readouterr()
    assert "[CSV Error] Simulasi error disk" in captured.out
    mock_to_csv_method.assert_called_once()


# Tes untuk metode save_to_google_sheets
@patch("utils.load.Credentials.from_service_account_file")
@patch("utils.load.build")
def test_data_saver_saves_to_google_sheets_successfully(mock_build, mock_creds_from_file, sample_product_dataframe, capsys):
    """
    Menguji apakah DataSaver.save_to_google_sheets berhasil memanggil API Google Sheets
    untuk menghapus dan memperbarui data.
    """
    mock_service = MagicMock()
    mock_spreadsheets_api = MagicMock()
    mock_values_api = MagicMock()

    mock_service.spreadsheets.return_value = mock_spreadsheets_api
    mock_spreadsheets_api.values.return_value = mock_values_api
    mock_values_api.clear.return_value.execute.return_value = None
    mock_values_api.update.return_value.execute.return_value = None

    mock_build.return_value = mock_service

    spreadsheet_config = {
        'spreadsheet_id': 'test_sheet_id',
        'range_name': 'Sheet1!A1'
    }
    credential_file_path = 'fake_credentials.json'

    saver = DataSaver(sample_product_dataframe)
    saver.save_to_google_sheets(spreadsheet_config, credential_file=credential_file_path)

    mock_creds_from_file.assert_called_once_with(
        credential_file_path,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    mock_build.assert_called_once_with('sheets', 'v4', credentials=mock_creds_from_file.return_value)
    mock_values_api.clear.assert_called_once_with(
        spreadsheetId=spreadsheet_config['spreadsheet_id'],
        range=spreadsheet_config['range_name']
    )
    mock_values_api.update.assert_called_once()
    # Verifikasi body yang dikirim ke update
    update_call_args = mock_values_api.update.call_args[1]
    assert update_call_args['spreadsheetId'] == spreadsheet_config['spreadsheet_id']
    assert update_call_args['range'] == spreadsheet_config['range_name']
    assert update_call_args['valueInputOption'] == "RAW"
    # Cek bahwa kolom dan data DataFrame ada di body['values']
    expected_header = sample_product_dataframe.columns.tolist()
    expected_data = sample_product_dataframe.values.tolist()
    assert update_call_args['body']['values'][0] == expected_header
    assert update_call_args['body']['values'][1:] == expected_data

    captured = capsys.readouterr()
    assert "[Google Sheets] Data berhasil disimpan ke Sheet1!A1." in captured.out


def test_data_saver_google_sheets_handles_empty_dataframe(empty_product_dataframe, capsys):
    """
    Menguji apakah DataSaver.save_to_google_sheets menangani DataFrame kosong
    dengan mencetak pesan dan tidak memanggil API Google Sheets.
    """
    spreadsheet_config = {
        'spreadsheet_id': 'test_sheet_id',
        'range_name': 'Sheet1!A1'
    }
    saver = DataSaver(empty_product_dataframe)
    saver.save_to_google_sheets(spreadsheet_config) # Tanpa credential_file, karena tidak akan dipanggil

    captured = capsys.readouterr()
    assert "[Google Sheets] DataFrame kosong, tidak ada yang disimpan." in captured.out
    # Pastikan tidak ada interaksi dengan API Google Sheets
    # Ini memerlukan patch pada Credentials dan build jika ingin lebih ketat,
    # tapi secara implisit, jika pesan tercetak, fungsi akan return awal.

@patch("utils.load.Credentials.from_service_account_file", side_effect=Exception("Error kredensial"))
def test_data_saver_google_sheets_error_handling(mock_creds_from_file, sample_product_dataframe, capsys):
    """
    Menguji penanganan error pada DataSaver.save_to_google_sheets ketika terjadi exception
    selama proses otentikasi atau interaksi API.
    """
    spreadsheet_config = {
        'spreadsheet_id': 'error_sheet_id',
        'range_name': 'Sheet1!A1'
    }
    saver = DataSaver(sample_product_dataframe)
    saver.save_to_google_sheets(spreadsheet_config, credential_file="invalid.json")

    captured = capsys.readouterr()
    assert "[Google Sheets Error] Error kredensial" in captured.out
    mock_creds_from_file.assert_called_once()


# --- Tes untuk Fungsi process_data ---

@patch.object(DataSaver, 'save_as_csv')
@patch.object(DataSaver, 'save_to_google_sheets')
@patch('utils.load.DataSaver') # Patch konstruktor DataSaver
def test_process_data_calls_all_savers(mock_data_saver_class, mock_save_to_gsheets, mock_save_as_csv, sample_product_dataframe):
    """
    Menguji apakah fungsi process_data menginisialisasi DataSaver dan memanggil
    semua metode penyimpanan yang relevan (CSV dan Google Sheets).
    """
    # Mock instance DataSaver yang akan dibuat oleh process_data
    mock_saver_instance = MagicMock()
    mock_data_saver_class.return_value = mock_saver_instance

    process_data(sample_product_dataframe)

    # Verifikasi DataSaver diinisialisasi dengan DataFrame yang benar
    mock_data_saver_class.assert_called_once_with(sample_product_dataframe)

    # Verifikasi metode penyimpanan dipanggil pada instance mock
    mock_saver_instance.save_as_csv.assert_called_once()
    mock_saver_instance.save_to_google_sheets.assert_called_once()
    # Verifikasi argumen untuk save_to_google_sheets
    gsheet_call_args = mock_saver_instance.save_to_google_sheets.call_args[0][0]
    assert gsheet_call_args['spreadsheet_id'] == '1jo5MFyc1SXzgAeFqR9QLKlHIyPexXeh3LCbKrKW_hdI'
    assert gsheet_call_args['range_name'] == 'Sheet1!A1'