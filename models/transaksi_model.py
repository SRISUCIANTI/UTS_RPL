from config.database import get_connection

class TransaksiModel:
    @staticmethod
    def hitungTotal(tarif_sewa, durasi_atau_jumlah):
        """Metode hitungTotal() sesuai katalog kelas"""
        return tarif_sewa * durasi_atau_jumlah

    @staticmethod
    def buatPesanan(id_user, tgl_sewa, tgl_kembali_rencana, total_biaya):
        """Metode buatPesanan() dengan pengamanan & cetak debug."""
        print(f"[DEBUG] Menerima id_user: {id_user}, tgl: {tgl_sewa}, total: {total_biaya}")
        conn = get_connection()
        if not conn:
            print("[ERROR] Koneksi database gagal.")
            return None
        cursor = conn.cursor()
        try:
            clean_id_user = int(str(id_user).strip())
            clean_total = float(str(total_biaya))
            
            cursor.execute(
                """INSERT INTO transaksi
                   (id_user, tgl_sewa, tgl_kembali_rencana, total_biaya, status_transaksi)
                   VALUES (%s, %s, %s, %s, 'Pending')""",
                (clean_id_user, tgl_sewa, tgl_kembali_rencana, clean_total)
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"[ERROR MySQL/Python] Buat Pesanan: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def catatDetail(id_transaksi, id_studio=None, id_alat=None, jumlah=1, subtotal=0,
                    jam_mulai=None, jam_selesai=None):
        """Catat satu baris item ke detail_transaksi.

        Tepat satu dari id_studio / id_alat yang diisi.
        jam_mulai/jam_selesai ('HH:MM') hanya untuk studio, NULL untuk alat.
        """
        if (id_studio is None) == (id_alat is None):
            print("[ERROR] Catat Detail: isi tepat satu dari id_studio / id_alat.")
            return False
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """INSERT INTO detail_transaksi
                   (id_transaksi, id_alat, id_studio, jumlah, subtotal, jam_mulai, jam_selesai)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (id_transaksi, id_alat, id_studio, jumlah, subtotal, jam_mulai, jam_selesai)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Catat Detail: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def catatDetailStudio(id_transaksi, id_studio, jumlah, subtotal,
                          jam_mulai=None, jam_selesai=None):
        """Kompatibilitas: catat sewa studio (delegasi ke catatDetail)."""
        return TransaksiModel.catatDetail(
            id_transaksi, id_studio=id_studio, jumlah=jumlah, subtotal=subtotal,
            jam_mulai=jam_mulai, jam_selesai=jam_selesai
        )

    @staticmethod
    def lihatDetail(id_transaksi):
        """Rincian item satu transaksi: nama studio/alat + qty + subtotal."""
        conn = get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT d.id_detail, d.jumlah, d.subtotal,
                          d.id_studio, s.nama_studio,
                          d.id_alat, a.nama_alat, a.harga_per_hari,
                          d.jam_mulai, d.jam_selesai
                   FROM detail_transaksi d
                   LEFT JOIN studio s ON s.id_studio = d.id_studio
                   LEFT JOIN alat a ON a.id_alat = d.id_alat
                   WHERE d.id_transaksi = %s
                   ORDER BY d.id_detail""",
                (id_transaksi,)
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Lihat Detail Transaksi: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def hapusTransaksi(id_transaksi):
        """Hapus transaksi + detailnya (rollback pemesanan yang gagal di tengah)."""
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM detail_transaksi WHERE id_transaksi = %s", (id_transaksi,))
            cursor.execute("DELETE FROM transaksi WHERE id_transaksi = %s", (id_transaksi,))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Hapus Transaksi: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def getById(id_transaksi):
        """Ambil satu transaksi + nama penyewa (untuk validasi bayar/kembali)."""
        conn = get_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT t.*, u.username, u.nama_lengkap
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
    def ubahStatus(id_transaksi, status_baru):
        """Metode ubahStatus() sesuai katalog kelas"""
        conn = get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE transaksi SET status_transaksi = %s WHERE id_transaksi = %s",
                (status_baru, id_transaksi)
            )
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Ubah Status Transaksi: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def _fetch_list(where_clause="", params=()):
        """Helper: ambil transaksi + nama penyewa + status pembayaran (skema asli DB).

        Satu baris per transaksi: bila ada beberapa pembayaran (sewa + denda),
        yang ditampilkan yang terbaru (id_pembayaran terbesar).
        """
        conn = get_connection()
        if not conn: return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                f"""SELECT t.id_transaksi, t.id_user, u.username, u.nama_lengkap,
                           t.tgl_sewa, t.tgl_kembali_rencana, t.tgl_kembali_aktual,
                           t.total_biaya, t.denda, t.status_transaksi,
                           p.id_pembayaran, p.metode_bayar, p.jumlah_bayar,
                           p.bukti_bayar,
                           p.status_konfirmasi AS status_pembayaran
                    FROM transaksi t
                    JOIN users u ON u.id_user = t.id_user
                    LEFT JOIN pembayaran p ON p.id_transaksi = t.id_transaksi
                        AND p.id_pembayaran = (SELECT MAX(p2.id_pembayaran)
                                               FROM pembayaran p2
                                               WHERE p2.id_transaksi = t.id_transaksi)
                    {where_clause}
                    ORDER BY t.id_transaksi DESC""",
                params
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Lihat Transaksi: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def lihatTagihanUser(id_user):
        """Pesanan milik user yang menunggu dibayar (Pending, belum ada bukti)."""
        conn = get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT t.* FROM transaksi t
                   LEFT JOIN pembayaran p ON p.id_transaksi = t.id_transaksi
                   WHERE t.id_user = %s AND t.status_transaksi = 'Pending'
                     AND p.id_pembayaran IS NULL
                   ORDER BY t.id_transaksi""",
                (id_user,)
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Lihat Tagihan: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def lihatPending():
        """Pesanan yang butuh tindakan operator: status Pending / pembayaran Menunggu."""
        return TransaksiModel._fetch_list(
            "WHERE t.status_transaksi = 'Pending' OR p.status_konfirmasi = 'Menunggu'"
        )

    @staticmethod
    def lihatRiwayat():
        """Riwayat: transaksi yang sudah selesai / lunas / tuntas / batal."""
        return TransaksiModel._fetch_list(
            "WHERE t.status_transaksi IN ('Selesai', 'Lunas', 'Batal', 'Tuntas')"
        )

    @staticmethod
    def lihatTagihanDendaUser(id_user):
        """Tagihan denda milik user: Selesai + denda>0, tanpa pembayaran Menunggu."""
        conn = get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT t.* FROM transaksi t
                    WHERE t.id_user = %s AND t.status_transaksi = 'Selesai'
                      AND t.denda > 0
                      AND NOT EXISTS (SELECT 1 FROM pembayaran p
                                      WHERE p.id_transaksi = t.id_transaksi
                                        AND p.status_konfirmasi = 'Menunggu')
                    ORDER BY t.id_transaksi""",
                (id_user,)
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Lihat Tagihan Denda: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def lihatRiwayatUser(id_user):
        """Semua pesanan milik satu penyewa (aktif + riwayat), terbaru dulu."""
        try:
            id_user = int(str(id_user).strip())
        except (ValueError, AttributeError):
            return []
        return TransaksiModel._fetch_list(
            "WHERE t.id_user = %s", (id_user,)
        )