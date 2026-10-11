# File: models/pembayaran_model.py
from config.database import get_connection

class PembayaranModel:
    @staticmethod
    def verifikasi(id_pembayaran, status_baru):
        """Metode verifikasi() untuk memproses konfirmasi manual pembayaran oleh operator"""
        conn = get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE pembayaran SET status_konfirmasi = %s WHERE id_pembayaran = %s",
                (status_baru, id_pembayaran)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Verifikasi Pembayaran Gagal: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def getById(id_pembayaran):
        """Ambil satu pembayaran berdasarkan ID."""
        conn = get_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM pembayaran WHERE id_pembayaran = %s",
                (id_pembayaran,)
            )
            return cursor.fetchone()
        except Exception as e:
            print(f"[ERROR] Ambil Pembayaran: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def getByTransaksi(id_transaksi):
        """Ambil pembayaran untuk satu transaksi (untuk cegah upload ganda)."""
        conn = get_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT * FROM pembayaran WHERE id_transaksi = %s ORDER BY id_pembayaran DESC LIMIT 1",
                (id_transaksi,)
            )
            return cursor.fetchone()
        except Exception as e:
            print(f"[ERROR] Ambil Pembayaran Transaksi: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def tambahPembayaran(id_transaksi, metode, bukti_pembayaran, jumlah_bayar=0):
        """Metode pendukung untuk mengunggah info pembayaran"""
        conn = get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO pembayaran (id_transaksi, metode_bayar, jumlah_bayar, bukti_bayar, status_konfirmasi) 
                   VALUES (%s, %s, %s, %s, 'Menunggu')""",
                (id_transaksi, metode, jumlah_bayar, bukti_pembayaran)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Tambah Pembayaran: {e}")
            return False
        finally:
            conn.close()