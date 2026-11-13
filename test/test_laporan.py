"""FR-06 (Dashboard Eksekutif: rekap & utilisasi) dan
FR-08 (Laporan Transaksi & Pendapatan + export TXT)."""
from decimal import Decimal
from unittest.mock import patch

from controllers.laporan_controller import LaporanController as LC
from models.laporan_model import LaporanModel

LM = "controllers.laporan_controller.LaporanModel"


# ---------- LaporanModel (FR-06) ----------
@patch("models.laporan_model.get_connection")
def test_rekap_umum_model_menggabungkan_pendapatan_dan_info_status(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.return_value = {"jml": 3, "sewa": Decimal("300000"), "denda": Decimal("40000")}
    cursor.fetchall.return_value = [
        {"status_transaksi": "Pending", "jml": 2},
        {"status_transaksi": "Batal", "jml": 1},
    ]

    hasil = LaporanModel.rekapUmum()

    assert hasil == {"jml_transaksi": 3, "total_sewa": 300000.0, "total_denda": 40000.0,
                     "pending": 2, "batal": 1}
    conn.close.assert_called_once()


@patch("models.laporan_model.get_connection")
def test_rekap_umum_model_tanpa_pending_dan_batal(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.return_value = {"jml": 0, "sewa": None, "denda": None}
    cursor.fetchall.return_value = []

    hasil = LaporanModel.rekapUmum()

    assert hasil["total_sewa"] == 0.0 and hasil["pending"] == 0 and hasil["batal"] == 0


@patch("models.laporan_model.get_connection")
def test_rekap_umum_model_pendapatan_hanya_status_lunas_selesai_tuntas(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchone.return_value = {"jml": 0, "sewa": 0, "denda": 0}
    cursor.fetchall.return_value = []

    LaporanModel.rekapUmum()

    sql = cursor.execute.call_args_list[0][0][0]
    assert "('Lunas', 'Selesai', 'Tuntas')" in sql
    assert "Pending" not in sql and "Batal" not in sql


@patch("models.laporan_model.get_connection", return_value=None)
def test_rekap_umum_model_koneksi_gagal_none(_):
    assert LaporanModel.rekapUmum() is None


@patch("models.laporan_model.get_connection")
def test_utilisasi_model_mengubah_tipe_angka(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchall.return_value = [
        {"kategori": "Studio", "nama": "Studio A", "frekuensi": 4, "pendapatan": Decimal("200000")},
        {"kategori": "Alat", "nama": "Easel", "frekuensi": 2, "pendapatan": None},
    ]

    hasil = LaporanModel.utilisasi()

    assert hasil[0]["pendapatan"] == 200000.0 and isinstance(hasil[0]["pendapatan"], float)
    assert hasil[1]["pendapatan"] == 0.0


@patch("models.laporan_model.get_connection")
def test_utilisasi_model_error_database_none(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.execute.side_effect = Exception("db error")
    assert LaporanModel.utilisasi() is None


@patch("models.laporan_model.get_connection")
def test_pendapatan_bulanan_model_dengan_filter_bulan(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchall.return_value = [{"bulan": "2026-11", "jml": 2, "sewa": Decimal("100000"),
                                     "denda": Decimal("0")}]

    hasil = LaporanModel.pendapatanBulanan("2026-11")

    assert cursor.execute.call_args[0][1] == ("2026-11",)
    assert hasil[0]["sewa"] == 100000.0


@patch("models.laporan_model.get_connection")
def test_riwayat_model_filter_status(mock_gc, fake_db):
    conn, cursor = fake_db(mock_gc)
    cursor.fetchall.return_value = []

    LaporanModel.riwayat("Lunas")
    assert cursor.execute.call_args[0][1] == ("Lunas",)

    LaporanModel.riwayat()
    assert len(cursor.execute.call_args[0]) == 1  # tanpa parameter = semua status


# ---------- LaporanController: rekap (FR-06) ----------
@patch(LM)
def test_rekap_umum_controller_total_sewa_ditambah_denda(lm):
    lm.rekapUmum.return_value = {"jml_transaksi": 3, "total_sewa": 300000.0,
                                 "total_denda": 40000.0, "pending": 2, "batal": 1}

    baris = LC.rekap_umum()

    teks = "\n".join(baris)
    assert "TOTAL PENDAPATAN" in teks and "340,000" in teks
    assert "Pending=2" in teks and "Batal=1" in teks


@patch(LM)
def test_rekap_umum_controller_database_gagal_none(lm):
    lm.rekapUmum.return_value = None
    assert LC.rekap_umum() is None


# ---------- LaporanController: riwayat (FR-08) ----------
RIWAYAT = [
    {"id_transaksi": 1, "tgl_sewa": "2026-11-05", "tgl_kembali_rencana": "2026-11-06",
     "tgl_kembali_aktual": None, "username": "kila", "nama_lengkap": "Kila",
     "total_biaya": 100000, "denda": 0, "status_transaksi": "Lunas"},
    {"id_transaksi": 2, "tgl_sewa": "2026-10-20", "tgl_kembali_rencana": "2026-10-21",
     "tgl_kembali_aktual": "2026-10-22", "username": "ana", "nama_lengkap": "Ana",
     "total_biaya": 50000, "denda": 20000, "status_transaksi": "Tuntas"},
]


@patch(LM)
def test_riwayat_semua_status(lm):
    lm.riwayat.return_value = list(RIWAYAT)

    baris = LC.riwayat_transaksi()

    assert baris[0] == "RIWAYAT TRANSAKSI"
    assert baris[1] == "Jumlah: 2 transaksi"
    assert len(baris) == 4
    lm.riwayat.assert_called_once_with(None)


@patch(LM)
def test_riwayat_filter_bulan_menyaring_berdasarkan_tgl_sewa(lm):
    lm.riwayat.return_value = list(RIWAYAT)

    baris = LC.riwayat_transaksi(bulan="2026-11")

    assert baris[1] == "Jumlah: 1 transaksi"
    assert "ID 1" in baris[2] and "2026-11" in baris[0]


@patch(LM)
def test_riwayat_filter_status_dinormalkan(lm):
    lm.riwayat.return_value = []

    baris = LC.riwayat_transaksi(status="lunas")

    lm.riwayat.assert_called_once_with("Lunas")
    assert "Tidak ada data." in baris


@patch(LM)
def test_riwayat_status_tidak_valid_none(lm):
    assert LC.riwayat_transaksi(status="Rusak") is None
    lm.riwayat.assert_not_called()


@patch(LM)
def test_riwayat_format_bulan_salah_none(lm):
    assert LC.riwayat_transaksi(bulan="11-2026") is None


# ---------- LaporanController: pendapatan bulanan (FR-08) ----------
@patch(LM)
def test_pendapatan_bulanan_menjumlahkan_total(lm):
    lm.pendapatanBulanan.return_value = [
        {"bulan": "2026-10", "jml": 2, "sewa": 100000.0, "denda": 20000.0},
        {"bulan": "2026-11", "jml": 1, "sewa": 50000.0, "denda": 0.0},
    ]

    baris = LC.pendapatan_bulanan()

    assert baris[0] == "PENDAPATAN BULANAN"
    assert "2026-10 | 2 transaksi" in baris[1]
    assert baris[-1] == "TOTAL | 3 transaksi | Rp170,000"


@patch(LM)
def test_pendapatan_bulanan_kosong(lm):
    lm.pendapatanBulanan.return_value = []

    baris = LC.pendapatan_bulanan("2026-01")

    assert baris[0] == "PENDAPATAN BULANAN - 2026-01"
    assert "Tidak ada data" in baris[1]


@patch(LM)
def test_pendapatan_bulanan_format_bulan_salah_none(lm):
    assert LC.pendapatan_bulanan("Januari") is None
    lm.pendapatanBulanan.assert_not_called()


# ---------- export TXT (FR-08) ----------
def test_simpan_txt_menulis_file_dengan_header_dan_isi(tmp_path):
    path = tmp_path / "laporan.txt"

    hasil = LC.simpan_txt("rekap", ["BARIS SATU", "BARIS DUA"], str(path))

    assert hasil == str(path)
    isi = path.read_text(encoding="utf-8")
    assert isi.startswith("ArtStudio-Rent | dicetak")
    assert "BARIS SATU\nBARIS DUA" in isi


def test_simpan_txt_lokasi_tidak_bisa_ditulis_mengembalikan_none(tmp_path):
    path = tmp_path / "folder_tidak_ada" / "laporan.txt"
    assert LC.simpan_txt("rekap", ["x"], str(path)) is None
