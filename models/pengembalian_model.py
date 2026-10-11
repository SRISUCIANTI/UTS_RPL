# models/pengembalian_model.py
from config.database import get_connection

class PengembalianModel:
    @staticmethod
    def hitungDenda(keterlambatan_hari, tarif_denda_per_hari=20000):
        """Metode hitungDenda() sesuai Katalog Kelas 4.7"""
        if keterlambatan_hari and keterlambatan_hari > 0:
            return keterlambatan_hari * tarif_denda_per_hari
        return 0

    @staticmethod
    def getTransaksi(id_transaksi):
        """Ambil satu transaksi + data penyewa untuk proses pengembalian."""
        conn = get_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT t.id_transaksi, t.id_user, u.username, u.nama_lengkap,
                          t.tgl_sewa, t.tgl_kembali_rencana, t.tgl_kembali_aktual,
                          t.total_biaya, t.denda, t.status_transaksi
                   FROM transaksi t
                   JOIN users u ON u.id_user = t.id_user
                   WHERE t.id_transaksi = %s""",
                (id_transaksi,)
            )
            return cursor.fetchone()
        except Exception as e:
            print(f"[ERROR] Ambil Transaksi: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def lihatBelumKembali():
        """Semua sewa aktif (status Lunas) yang belum dikembalikan.

        Dipakai menu operator agar tidak perlu hafal / ketik ID manual.
        """
        conn = get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT t.id_transaksi, t.id_user, u.username, u.nama_lengkap,
                          t.tgl_sewa, t.tgl_kembali_rencana, t.tgl_kembali_aktual,
                          t.total_biaya, t.denda, t.status_transaksi,
                          DATEDIFF(CURDATE(), t.tgl_kembali_rencana) AS hari_terlambat
                   FROM transaksi t
                   JOIN users u ON u.id_user = t.id_user
                   WHERE t.status_transaksi = 'Lunas'
                   ORDER BY t.tgl_kembali_rencana ASC"""
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Lihat Belum Kembali: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def prosesPengembalian(id_transaksi, tanggal_kembali_aktual, denda):
        """Mencatat pengembalian langsung di tabel transaksi.

        (Tidak ada tabel `pengembalian` di DB — skema asli memakai
        kolom tgl_kembali_aktual + denda + status_transaksi='Selesai'.)
        """
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """UPDATE transaksi
                   SET tgl_kembali_aktual = %s, denda = %s, status_transaksi = 'Selesai'
                   WHERE id_transaksi = %s""",
                (tanggal_kembali_aktual, denda, id_transaksi)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Proses Pengembalian: {e}")
            return False
        finally:
            conn.close()
