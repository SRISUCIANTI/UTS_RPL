# models/laporan_model.py
from config.database import get_connection

# Status yang uangnya sudah diterima (masuk pendapatan) vs yang dikecualikan.
# Sewa dihitung untuk Lunas+Selesai+Tuntas; denda hanya yang sudah dibayar
# (Tuntas). Selesai-berdenda belum dihitung dendanya sampai Tuntas.
STATUS_PENDAPATAN = ('Lunas', 'Selesai', 'Tuntas')


class LaporanModel:
    @staticmethod
    def rekapUmum():
        """Rekapitulasi: pendapatan (Lunas+Selesai+Tuntas) + info Pending/Batal.

        Denda hanya dihitung yang sudah dibayar (status Tuntas).
        """
        conn = get_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT COUNT(*) AS jml, COALESCE(SUM(total_biaya), 0) AS sewa,
                          COALESCE(SUM(CASE WHEN status_transaksi = 'Tuntas' THEN denda ELSE 0 END), 0) AS denda
                    FROM transaksi WHERE status_transaksi IN ('Lunas', 'Selesai', 'Tuntas')"""
            )
            masuk = cursor.fetchone()
            cursor.execute(
                """SELECT status_transaksi, COUNT(*) AS jml
                   FROM transaksi WHERE status_transaksi IN ('Pending', 'Batal')
                   GROUP BY status_transaksi"""
            )
            luar = {r['status_transaksi']: r['jml'] for r in cursor.fetchall()}
            return {
                'jml_transaksi': masuk['jml'] or 0,
                'total_sewa': float(masuk['sewa'] or 0),
                'total_denda': float(masuk['denda'] or 0),
                'pending': luar.get('Pending', 0),
                'batal': luar.get('Batal', 0),
            }
        except Exception as e:
            print(f"[ERROR] Rekap Umum: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def riwayat(status=None):
        """Riwayat transaksi sewa + nama penyewa. status: None = semua."""
        conn = get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            if status:
                cursor.execute(
                    """SELECT t.id_transaksi, t.tgl_sewa, t.tgl_kembali_rencana,
                              t.tgl_kembali_aktual, t.total_biaya, t.denda,
                              t.status_transaksi, u.username, u.nama_lengkap
                       FROM transaksi t
                       JOIN users u ON u.id_user = t.id_user
                       WHERE t.status_transaksi = %s
                       ORDER BY t.tgl_sewa DESC, t.id_transaksi DESC""",
                    (status,)
                )
            else:
                cursor.execute(
                    """SELECT t.id_transaksi, t.tgl_sewa, t.tgl_kembali_rencana,
                              t.tgl_kembali_aktual, t.total_biaya, t.denda,
                              t.status_transaksi, u.username, u.nama_lengkap
                       FROM transaksi t
                       JOIN users u ON u.id_user = t.id_user
                       ORDER BY t.tgl_sewa DESC, t.id_transaksi DESC"""
                )
            return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Riwayat Transaksi: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def pendapatanBulanan(bulan=None):
        """Pendapatan per bulan (YYYY-MM) dari tgl_sewa. bulan=None = semua.

        Mengembalikan list dict: {bulan, jml, sewa, denda}.
        """
        conn = get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            if bulan:
                cursor.execute(
                    """SELECT DATE_FORMAT(tgl_sewa, '%Y-%m') AS bulan, COUNT(*) AS jml,
                              COALESCE(SUM(total_biaya), 0) AS sewa,
                              COALESCE(SUM(CASE WHEN status_transaksi = 'Tuntas' THEN denda ELSE 0 END), 0) AS denda
                        FROM transaksi
                        WHERE status_transaksi IN ('Lunas', 'Selesai', 'Tuntas')
                          AND DATE_FORMAT(tgl_sewa, '%Y-%m') = %s
                        GROUP BY bulan""",
                    (bulan,)
                )
            else:
                cursor.execute(
                    """SELECT DATE_FORMAT(tgl_sewa, '%Y-%m') AS bulan, COUNT(*) AS jml,
                              COALESCE(SUM(total_biaya), 0) AS sewa,
                              COALESCE(SUM(CASE WHEN status_transaksi = 'Tuntas' THEN denda ELSE 0 END), 0) AS denda
                        FROM transaksi
                        WHERE status_transaksi IN ('Lunas', 'Selesai', 'Tuntas')
                        GROUP BY bulan ORDER BY bulan"""
                )
            rows = cursor.fetchall()
            for r in rows:
                r['sewa'] = float(r['sewa'] or 0)
                r['denda'] = float(r['denda'] or 0)
            return rows
        except Exception as e:
            print(f"[ERROR] Pendapatan Bulanan: {e}")
            return []
        finally:
            conn.close()
