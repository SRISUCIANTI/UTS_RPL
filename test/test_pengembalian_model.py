import pytest
from unittest.mock import MagicMock, patch

from models.pengembalian_model import PengembalianModel


@pytest.mark.parametrize(
    "telat, harapan",
    [
        (0, 0),          # tepat waktu
        (-3, 0),         # kembali lebih awal
        (None, 0),       # tanggal tidak ada
        (1, 20000),      # satu hari
        (3, 60000),      # tiga hari
    ],
)
def test_hitung_denda_tarif_20000_per_hari(telat, harapan):
    assert PengembalianModel.hitungDenda(telat) == harapan


def test_hitung_denda_dengan_tarif_khusus():
    assert PengembalianModel.hitungDenda(2, tarif_denda_per_hari=5000) == 10000


@patch("models.pengembalian_model.get_connection")
def test_proses_pengembalian_menyimpan_denda_dan_status_selesai(mock_get_connection):
    conn, cursor = MagicMock(), MagicMock()
    conn.cursor.return_value = cursor
    mock_get_connection.return_value = conn
    cursor.rowcount = 1

    hasil = PengembalianModel.prosesPengembalian(12, "2026-11-20", 40000)

    assert hasil is True
    sql, params = cursor.execute.call_args[0]
    assert "status_transaksi = 'Selesai'" in sql
    assert params == ("2026-11-20", 40000, 12)
    conn.commit.assert_called_once()
    conn.close.assert_called_once()


@patch("models.pengembalian_model.get_connection")
def test_proses_pengembalian_transaksi_tidak_ada(mock_get_connection):
    conn, cursor = MagicMock(), MagicMock()
    conn.cursor.return_value = cursor
    mock_get_connection.return_value = conn
    cursor.rowcount = 0  # tidak ada baris yang berubah

    assert PengembalianModel.prosesPengembalian(999, "2026-11-20", 0) is False


@patch("models.pengembalian_model.get_connection", return_value=None)
def test_proses_pengembalian_koneksi_gagal(_):
    assert PengembalianModel.prosesPengembalian(1, "2026-11-20", 0) is False
