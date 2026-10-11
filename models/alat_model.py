from config.database import get_connection

class AlatModel:
    @staticmethod
    def lihatSemua():
        """Daftar semua alat untuk katalog (skema asli DB)."""
        conn = get_connection()
        if not conn:
            return []
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM alat ORDER BY id_alat")
            return cursor.fetchall()
        except Exception as e:
            print(f"[ERROR] Lihat Alat: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def cekKetersediaan(id_alat):
        """Metode cekKetersediaan() sesuai katalog kelas (kolom asli DB)."""
        conn = get_connection()
        if not conn:
            return None
        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT * FROM alat WHERE id_alat = %s", (id_alat,))
            return cursor.fetchone()
        except Exception as e:
            print(f"[ERROR] Cek Alat: {e}")
            return None
        finally:
            conn.close()

    @staticmethod
    def ubahStok(id_alat, delta):
        """Tambah/kurangi stok fisik alat (delta negatif = kurangi saat dipesan)."""
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            if delta < 0:
                cursor.execute(
                    "UPDATE alat SET stok = stok + %s WHERE id_alat = %s AND stok + %s >= 0",
                    (delta, id_alat, delta)
                )
            else:
                cursor.execute(
                    "UPDATE alat SET stok = stok + %s WHERE id_alat = %s",
                    (delta, id_alat)
                )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"[ERROR] Ubah Stok Alat: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def kelolaData(action, id_alat=None, nama_alat="", kategori="", stok=0, tarif_sewa=0):
        """Metode kelolaData() untuk Tambah/Ubah/Hapus (CRUD)."""
        conn = get_connection()
        if not conn:
            return False
        cursor = conn.cursor()
        try:
            if action == 'tambah':
                cursor.execute(
                    "INSERT INTO alat (nama_alat, harga_per_hari, stok, deskripsi) VALUES (%s, %s, %s, %s)",
                    (nama_alat, tarif_sewa, stok, kategori or None)
                )
            elif action == 'update':
                cursor.execute(
                    "UPDATE alat SET nama_alat=%s, harga_per_hari=%s, stok=%s, deskripsi=%s WHERE id_alat=%s",
                    (nama_alat, tarif_sewa, stok, kategori or None, id_alat)
                )
            elif action == 'hapus':
                cursor.execute("DELETE FROM alat WHERE id_alat=%s", (id_alat,))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] Kelola Data Alat: {e}")
            return False
        finally:
            conn.close()
