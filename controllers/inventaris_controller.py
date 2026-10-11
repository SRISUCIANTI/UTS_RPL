from models.alat_model import AlatModel
from models.studio_model import StudioModel

class InventarisController:
    # --- LOGIKA ALAT ---
    @staticmethod
    def lihat_semua_alat():
        """Mengambil daftar seluruh alat untuk katalog"""
        return AlatModel.lihatSemua()

    @staticmethod
    def kelola_alat(action, id_alat=None, nama_alat="", kategori="", stok=0, tarif_sewa=0):
        """Menangani aksi Tambah, Edit, atau Hapus Alat (CRUD)"""
        if action in ['tambah', 'update'] and (not nama_alat or tarif_sewa <= 0):
            return False, "Nama alat dan tarif sewa harus valid!"
        try:
            _stok = int(stok or 0)
        except (ValueError, TypeError):
            return False, "Stok harus angka!"
        if action in ['tambah', 'update'] and _stok < 0:
            return False, "Stok tidak boleh negatif!"
        
        success = AlatModel.kelolaData(action, id_alat, nama_alat, kategori, stok, tarif_sewa)
        if success:
            return True, f"Berhasil {action} data alat."
        return False, f"Gagal {action} data alat."

    # --- LOGIKA STUDIO ---
    STATUS_STUDIO_VALID = ('Tersedia', 'Dibooking', 'Maintenance')

    @staticmethod
    def lihat_semua_studio():
        """Mengambil seluruh data studio untuk katalog"""
        return StudioModel.lihatSemua()

    _BULAN = ('', 'Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun',
              'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des')

    @staticmethod
    def tampil_jam(nilai):
        """'09:00:00'/timedelta/time -> '09.00'. Tahan jam 1 digit & '24:00:00'.

        MySQL TIME '24:00:00' terbaca sebagai timedelta 1 hari
        (str = '1 day, 0:00:00'), jadi hitung dari total detik.
        Format tak dikenal -> '--.--' (tidak pernah crash).
        """
        try:
            if hasattr(nilai, 'total_seconds'):
                total_menit = int(nilai.total_seconds() // 60)
            elif hasattr(nilai, 'hour'):
                total_menit = nilai.hour * 60 + nilai.minute
            else:
                p = str(nilai).strip().split(':')
                if len(p) < 2:
                    return '--.--'
                # sisa hari ala '1 day, 0' (dari timedelta 24 jam)
                jam_txt = p[0].split(',')[-1].strip().split()[-1]
                total_menit = int(jam_txt) * 60 + int(p[1])
            return f"{total_menit // 60:02d}.{total_menit % 60:02d}"
        except (ValueError, TypeError, IndexError, AttributeError):
            return '--.--'

    @staticmethod
    def jadwal_studio(id_studio):
        """Jadwal terisi satu studio, bahasa sederhana, tanpa nama penyewa."""
        hasil = []
        for j in StudioModel.jadwalStudio(id_studio):
            tgl = f"{j['tgl_sewa'].day} {InventarisController._BULAN[j['tgl_sewa'].month]}"
            if j.get('jam_mulai') is not None and j.get('jam_selesai') is not None:
                mulai = InventarisController.tampil_jam(j['jam_mulai'])
                selesai = InventarisController.tampil_jam(j['jam_selesai'])
                hasil.append(f"{tgl}, jam {mulai}-{selesai}")
            else:
                hasil.append(f"{tgl} (sehari penuh)")
        return hasil

    @staticmethod
    def jadwal_hari_ini(id_studio):
        """Booking hari ini satu studio (jam saja), untuk bantu operator nilai full/tidak."""
        from datetime import date
        hari_ini = date.today()
        hasil = []
        for j in StudioModel.jadwalStudio(id_studio):
            tgl_mulai = j.get('tgl_sewa')
            tgl_selesai = j.get('tgl_kembali_rencana') or tgl_mulai
            if tgl_mulai is None:
                continue
            # tgl bisa date/datetime/str tergantung driver; samakan ke date
            try:
                d_mulai = tgl_mulai.date() if hasattr(tgl_mulai, 'date') and not isinstance(tgl_mulai, date) else tgl_mulai
                d_selesai = tgl_selesai.date() if hasattr(tgl_selesai, 'date') and not isinstance(tgl_selesai, date) else tgl_selesai
                if isinstance(d_mulai, str):
                    from datetime import datetime as _dt
                    d_mulai = _dt.strptime(str(d_mulai)[:10], "%Y-%m-%d").date()
                if isinstance(d_selesai, str):
                    from datetime import datetime as _dt
                    d_selesai = _dt.strptime(str(d_selesai)[:10], "%Y-%m-%d").date()
            except (ValueError, TypeError, AttributeError):
                continue
            if d_mulai <= hari_ini <= d_selesai:
                if j.get('jam_mulai') is not None and j.get('jam_selesai') is not None:
                    hasil.append(f"{InventarisController.tampil_jam(j['jam_mulai'])}-{InventarisController.tampil_jam(j['jam_selesai'])}")
                else:
                    hasil.append("sehari penuh")
        return hasil

    @staticmethod
    def atur_status_studio(id_studio, status_baru):
        """Mengubah status ketersediaan studio.

        Tersedia = buka (jadwal per-jam tetap dicek).
        Dibooking = tutup manual / full hari ini oleh operator (blokir semua tanggal
            sampai dibuka lagi ke Tersedia).
        Maintenance = tutup perawatan (blokir total).
        """
        try:
            id_studio = int(str(id_studio).strip())
        except (ValueError, AttributeError):
            return False, "ID Studio harus angka."
        status_baru = str(status_baru).strip().capitalize()
        if status_baru not in InventarisController.STATUS_STUDIO_VALID:
            return False, "Status harus Tersedia, Dibooking, atau Maintenance."

        studio = StudioModel.getById(id_studio)
        if not studio:
            return False, f"Studio ID {id_studio} tidak ditemukan."
        if studio['status_ketersediaan'] == status_baru:
            return False, f"Studio '{studio['nama_studio']}' sudah berstatus {status_baru}."

        if StudioModel.ubahStatus(id_studio, status_baru):
            tambahan = "."
            if status_baru == 'Dibooking':
                tambahan = " (tutup full sementara — ingat kembalikan ke Tersedia besok!)."
            elif status_baru == 'Tersedia' and studio['status_ketersediaan'] == 'Dibooking':
                tambahan = " (sudah dibuka lagi, penyewa bisa booking per jam)."
            elif status_baru == 'Tersedia':
                tambahan = " (penyewa bisa booking per jam)."
            return True, f"Status '{studio['nama_studio']}' diubah {studio['status_ketersediaan']} -> {status_baru}{tambahan}"
        return False, "Gagal mengubah status studio (database)."

    @staticmethod
    def kelola_studio(action, id_studio=None, nama_studio="", kapasitas=0, tarif_sewa=0, fasilitas=None, status_ketersediaan=None):
        """Menangani aksi Tambah, Edit, atau Hapus Studio (CRUD)"""
        if action in ['tambah', 'update'] and (not nama_studio or tarif_sewa <= 0):
            return False, "Nama studio dan tarif sewa harus valid!"
        try:
            _kap = int(kapasitas or 0)
        except (ValueError, TypeError):
            return False, "Kapasitas harus angka!"
        if action in ['tambah', 'update'] and _kap <= 0:
            return False, "Kapasitas harus lebih dari 0!"
        if action == 'hapus':
            return InventarisController.hapus_studio(id_studio)
        if status_ketersediaan is None:
            if action == 'update' and id_studio:
                cur = StudioModel.getById(id_studio)
                status_ketersediaan = cur['status_ketersediaan'] if cur else 'Tersedia'
            else:
                status_ketersediaan = 'Tersedia'
        
        success = StudioModel.kelolaData(action, id_studio, nama_studio, kapasitas, tarif_sewa, fasilitas, status_ketersediaan)
        if success:
            return True, f"Berhasil {action} data studio."
        return False, f"Gagal {action} data studio."

    @staticmethod
    def hapus_studio(id_studio):
        """Hapus studio bila aman: ada, tanpa booking aktif, tanpa riwayat pakai."""
        try:
            id_studio = int(str(id_studio).strip())
        except (ValueError, AttributeError):
            return False, "ID Studio harus angka."
        studio = StudioModel.getById(id_studio)
        if not studio:
            return False, f"Studio ID {id_studio} tidak ditemukan."
        if StudioModel.adaBookingAktif(id_studio):
            return False, (f"Studio '{studio['nama_studio']}' masih ada booking aktif "
                            "(Pending/Lunas). Selesaikan/batalkan dulu atau pakai menu 7 -> Maintenance.")
        dipakai = StudioModel.hitungPemakaian(id_studio)
        if dipakai < 0:
            return False, "Gagal mengecek riwayat studio (database)."
        if dipakai > 0:
            return False, (f"Studio '{studio['nama_studio']}' sudah pernah disewa ({dipakai}x). "
                            "Tidak bisa dihapus agar riwayat tidak rusak. Pakai menu 7 -> Maintenance saja.")
        if StudioModel.kelolaData('hapus', id_studio):
            return True, f"Studio '{studio['nama_studio']}' berhasil dihapus."
        return False, "Gagal menghapus studio (database)."