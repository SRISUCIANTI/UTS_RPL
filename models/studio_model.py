from config.database import get_connection

class StudioModel:
    @staticmethod
    def getById(id_studio):
        """Ambil satu studio berdasarkan ID (skema asli DB)."""
        conn = get_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM studio WHERE id_studio = %s", (id_studio,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[ERROR] Ambil Studio: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def lihatSemua():
        """Daftar semua studio untuk katalog (skema asli DB)."""
        conn = get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM studio ORDER BY id_studio")
            return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Lihat Studio: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def cekJadwal(id_studio, tgl_mulai, tgl_selesai, jam_mulai=None, jam_selesai=None):
        """Metode cekJadwal(): True jika studio bisa dipesan pada tanggal + jam.

        Menolak studio Maintenance (perawatan) dan Dibooking (tutup manual /
        full hari ini oleh operator), dan menolak bila ada transaksi Lunas
        yang tanggalnya bersinggungan DAN jamnya bersinggungan.
        Hanya Lunas yang mengunci slot (Pending tak-bayar tidak menahan).
        Beda jam di tanggal sama = boleh. Baris lama tanpa jam (NULL)
        dianggap memenuhi seharian.
        Jam format 'HH:MM'. Tanpa jam = cek tanggal saja (mode lama).
        """
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT status_ketersediaan FROM studio WHERE id_studio = %s",
                (id_studio,)
            )
            studio = cursor.fetchone()
            if not studio:
                return False
            if studio['status_ketersediaan'] in ('Maintenance', 'Dibooking'):
                return False
            if jam_mulai and jam_selesai:
                cursor.execute(
                    """SELECT t.id_transaksi FROM transaksi t
                       JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                       WHERE d.id_studio = %s
                         AND t.status_transaksi = 'Lunas'
                         AND NOT (t.tgl_kembali_rencana < %s OR t.tgl_sewa > %s)
                         AND (d.jam_mulai IS NULL OR d.jam_selesai IS NULL
                              OR NOT (d.jam_selesai <= %s OR d.jam_mulai >= %s))
                       LIMIT 1""",
                    (id_studio, tgl_mulai, tgl_selesai, jam_mulai, jam_selesai)
                )
            else:
                cursor.execute(
                    """SELECT t.id_transaksi FROM transaksi t
                       JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                       WHERE d.id_studio = %s
                         AND t.status_transaksi = 'Lunas'
                         AND NOT (t.tgl_kembali_rencana < %s OR t.tgl_sewa > %s)
                       LIMIT 1""",
                    (id_studio, tgl_mulai, tgl_selesai)
                )
            bentrok = cursor.fetchone()
            return True if not bentrok else False  # True jika jadwal kosong
        except Exception as e:
            print(f"[ERROR] Cek Jadwal Studio: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def jadwalStudio(id_studio):
        """Jadwal terisi satu studio (tanpa nama penyewa, untuk layar user).

        Hanya booking Lunas masa kini & depan (tgl_kembali_rencana >= hari ini).
        Pending tidak mengunci slot sehingga tidak ditampilkan; yang sudah
        lewat tidak ditampilkan (realtime saat booking), data DB tetap utuh.
        """
        conn = get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                """SELECT t.tgl_sewa, t.tgl_kembali_rencana, d.jam_mulai, d.jam_selesai
                   FROM transaksi t
                   JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                   WHERE d.id_studio = %s
                     AND t.status_transaksi = 'Lunas'
                     AND t.tgl_kembali_rencana >= CURDATE()
                   ORDER BY t.tgl_sewa, d.jam_mulai""",
                (id_studio,)
            )
            return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Jadwal Studio: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def ubahStatus(id_studio, status_baru):
        """Ubah status ketersediaan studio (Tersedia/Dibooking/Maintenance)."""
        if status_baru not in ('Tersedia', 'Dibooking', 'Maintenance'):
            return False
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE studio SET status_ketersediaan = %s WHERE id_studio = %s",
                (status_baru, id_studio)
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Ubah Status Studio: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def hitungPemakaian(id_studio):
        """Hitung berapa baris detail_transaksi yang memakai studio ini (riwayat)."""
        conn = get_connection()
        if not conn:
            return -1
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM detail_transaksi WHERE id_studio = %s",
                (id_studio,)
            )
            row = cursor.fetchone()
            return int(row[0]) if row else 0
        except Exception as e:
            print(f"[ERROR] Hitung Pemakaian Studio: {e}")
            return -1
        finally:
            conn.close()

    @staticmethod
    def adaBookingAktif(id_studio):
        """True bila studio masih dipakai transaksi aktif (selain Batal/Selesai)."""
        conn = get_connection()
        if not conn:
            return True  # anggap ada demi keamanan (tolak hapus bila DB mati)
        cursor = conn.cursor()
        try:
            cursor.execute(
                """SELECT COUNT(*) FROM transaksi t
                   JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                   WHERE d.id_studio = %s
                     AND t.status_transaksi NOT IN ('Batal', 'Selesai')""",
                (id_studio,)
            )
            row = cursor.fetchone()
            return int(row[0]) > 0 if row else False
        except Exception as e:
            print(f"[ERROR] Cek Booking Aktif: {e}")
            return True
        finally:
            conn.close()

    @staticmethod
    def kelolaData(action, id_studio=None, nama_studio="", kapasitas=0, tarif_sewa=0,
                   fasilitas=None, status_ketersediaan='Tersedia'):
        """Metode kelolaData() untuk CRUD Studio (kolom asli: harga_per_jam)."""
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            if action == 'tambah':
                cursor.execute(
                    "INSERT INTO studio (nama_studio, harga_per_jam, kapasitas, fasilitas, status_ketersediaan) "
                    "VALUES (%s, %s, %s, %s, %s)",
                    (nama_studio, tarif_sewa, kapasitas, fasilitas, status_ketersediaan)
                )
            elif action == 'update':
                cursor.execute(
                    "UPDATE studio SET nama_studio=%s, harga_per_jam=%s, kapasitas=%s, fasilitas=%s, "
                    "status_ketersediaan=%s WHERE id_studio=%s",
                    (nama_studio, tarif_sewa, kapasitas, fasilitas, status_ketersediaan, id_studio)
                )
                if cursor.rowcount == 0:
                    conn.commit()
                    return False
            elif action == 'hapus':
                cursor.execute("DELETE FROM studio WHERE id_studio=%s", (id_studio,))
                if cursor.rowcount == 0:
                    conn.commit()
                    return False
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Kelola Data Studio: {e}")
            return False
        finally:
            conn.close()
