from datetime import datetime
from models.transaksi_model import TransaksiModel
from models.studio_model import StudioModel
from models.alat_model import AlatModel
from models.pembayaran_model import PembayaranModel

class TransaksiController:
    METODE_BAYAR_VALID = ('Tunai', 'Transfer')

    @staticmethod
    def _tanggal(tgl_sewa, tgl_kembali_rencana):
        """Parse sewa & kembali (YYYY-MM-DD). Kembalikan (d_sewa, d_kembali) / (None, pesan)."""
        try:
            d_sewa = datetime.strptime(str(tgl_sewa).strip(), "%Y-%m-%d").date()
            d_kembali = datetime.strptime(str(tgl_kembali_rencana).strip(), "%Y-%m-%d").date()
        except ValueError:
            return None, "Format tanggal salah. Gunakan YYYY-MM-DD (contoh: 2026-10-12)."
        if d_sewa < datetime.now().date():
            return None, (
                f"Tanggal sewa tidak boleh masa lalu (hari ini: {datetime.now().date()})."
            )
        if d_kembali < d_sewa:
            return None, "Tanggal rencana kembali tidak boleh sebelum tanggal sewa."
        return (d_sewa, d_kembali), None

    JAM_TUTUP = 22  # toko tutup 22.00, booking maks sampai jam ini

    @staticmethod
    def _jam(jam_mulai, durasi_jam):
        """Validasi jam mulai (0-23) + durasi. Kembalikan ('HH:MM', 'HH:MM', durasi) / (None, pesan)."""
        try:
            mulai = int(str(jam_mulai).strip())
            durasi = int(str(durasi_jam).strip())
        except (ValueError, AttributeError):
            return None, "Jam mulai dan durasi harus angka."
        if not 0 <= mulai <= 23:
            return None, "Jam mulai 0-21 (contoh: 9 untuk 09.00, karena tutup 22.00)."
        if durasi <= 0:
            return None, "Durasi harus lebih dari 0 jam."
        if mulai + durasi > TransaksiController.JAM_TUTUP:
            return None, (
                f"Toko tutup jam {TransaksiController.JAM_TUTUP:02d}.00 "
                f"(mulai {mulai:02d}.00 + {durasi} jam = {mulai + durasi:02d}.00, kelebihan)."
            )
        return ("%02d:00" % mulai, "%02d:00" % (mulai + durasi), durasi), None

    @staticmethod
    def proses_pesan_studio(id_user, id_studio, tgl_sewa, jam_mulai, durasi_jam):
        """Sewa studio per tanggal + jam. Kembali otomatis = tanggal sewa."""
        try:
            id_studio = int(str(id_studio).strip())
        except (ValueError, AttributeError):
            return False, "ID Studio harus angka."
        parsed, err = TransaksiController._tanggal(tgl_sewa, tgl_sewa)
        if err:
            return False, err
        d_sewa = parsed[0]
        tgl_s = d_sewa.strftime("%Y-%m-%d")
        jam, err = TransaksiController._jam(jam_mulai, durasi_jam)
        if err:
            return False, err
        mulai_s, selesai_s, jam_n = jam

        # Jam hari ini: hanya boleh pesan jam sekarang ke depan (blok penuh per jam).
        sekarang = datetime.now()
        if d_sewa == sekarang.date() and int(mulai_s[:2]) <= sekarang.hour:
            return False, (
                f"Sudah lewat jam {mulai_s.replace(':', '.')}. "
                f"Sekarang jam {sekarang.strftime('%H.%M')} — pilih jam mulai setelah itu."
            )

        studio = StudioModel.getById(id_studio)
        if not studio:
            return False, f"Studio ID {id_studio} tidak ditemukan."
        if studio.get('status_ketersediaan') == 'Maintenance':
            return False, f"'{studio['nama_studio']}' tutup (perawatan). Pilih studio lain."
        if studio.get('status_ketersediaan') == 'Dibooking':
            return False, (
                f"'{studio['nama_studio']}' tutup sementara oleh operator. "
                "Hubungi operator untuk info buka."
            )
        if not StudioModel.cekJadwal(id_studio, tgl_s, tgl_s, mulai_s, selesai_s):
            return False, (
                f"Studio penuh {tgl_s} jam {mulai_s.replace(':', '.')}-{selesai_s.replace(':', '.')} "
                "(jam bentrok dengan booking lain, pilih jam lain)!"
            )
        total = TransaksiModel.hitungTotal(float(studio['harga_per_jam']), jam_n)

        id_transaksi = TransaksiModel.buatPesanan(id_user, tgl_s, tgl_s, total)
        if not id_transaksi:
            return False, "Gagal membuat pesanan (database)."
        if not TransaksiModel.catatDetail(
            id_transaksi, id_studio=id_studio, jumlah=jam_n, subtotal=total,
            jam_mulai=mulai_s, jam_selesai=selesai_s
        ):
            TransaksiModel.hapusTransaksi(id_transaksi)
            return False, "Gagal mencatat detail studio."

        return True, "\n".join([
            "Pesanan studio berhasil dibuat!",
            f"Kode pesanan: {id_transaksi}",
            f"- {studio['nama_studio']}: {tgl_s} jam {mulai_s.replace(':', '.')}-{selesai_s.replace(':', '.')} "
            f"({jam_n} jam x Rp{float(studio['harga_per_jam']):,.0f}) = Rp{total:,.0f}",
            f"Total bayar: Rp{total:,.0f}.",
            "Langkah berikutnya: bayar di menu Bayar Pesanan.",
        ])

    @staticmethod
    def proses_pesan_alat(id_user, tgl_sewa, tgl_kembali_rencana, daftar_alat):
        """Sewa alat saja (cek stok). Harga = harian x jumlah x durasi hari."""
        daftar_alat = daftar_alat or []
        if not daftar_alat:
            return False, "Pilih minimal satu alat."
        parsed, err = TransaksiController._tanggal(tgl_sewa, tgl_kembali_rencana)
        if err:
            return False, err
        d_sewa, d_kembali = parsed
        durasi_hari = (d_kembali - d_sewa).days or 1
        tgl_sewa_s = d_sewa.strftime("%Y-%m-%d")
        tgl_kembali_s = d_kembali.strftime("%Y-%m-%d")

        item_alat = []
        for id_alat, qty in daftar_alat:
            try:
                id_alat = int(str(id_alat).strip())
                qty = int(str(qty).strip())
            except (ValueError, AttributeError):
                return False, f"ID/jumlah alat tidak valid: {id_alat} x {qty}."
            if qty <= 0:
                return False, f"Jumlah alat ID {id_alat} harus lebih dari 0."
            alat = AlatModel.cekKetersediaan(id_alat)
            if not alat:
                return False, f"Alat ID {id_alat} tidak ditemukan."
            if (alat['stok'] or 0) < qty:
                return False, f"Stok '{alat['nama_alat']}' kurang (sisa {alat['stok']}, minta {qty})."
            sub = TransaksiModel.hitungTotal(
                TransaksiModel.hitungTotal(float(alat['harga_per_hari']), qty), durasi_hari
            )
            item_alat.append((alat, qty, sub))

        total_biaya = sum(sub for _, _, sub in item_alat)
        id_transaksi = TransaksiModel.buatPesanan(id_user, tgl_sewa_s, tgl_kembali_s, total_biaya)
        if not id_transaksi:
            return False, "Gagal membuat pesanan (database)."

        stok_terpotong = []
        gagal = None
        for alat, qty, sub in item_alat:
            if not AlatModel.ubahStok(alat['id_alat'], -qty):
                gagal = f"stok '{alat['nama_alat']}' berubah/habis saat diproses."
                break
            stok_terpotong.append((alat['id_alat'], qty))
            if not TransaksiModel.catatDetail(
                id_transaksi, id_alat=alat['id_alat'], jumlah=qty, subtotal=sub
            ):
                gagal = "gagal mencatat detail alat."
                break
        if gagal:
            for aid, qty in stok_terpotong:
                AlatModel.ubahStok(aid, qty)
            TransaksiModel.hapusTransaksi(id_transaksi)
            return False, f"Pemesanan dibatalkan ({gagal} Stok dikembalikan. Coba lagi / kurangi jumlah)."

        baris = ["Pesanan alat berhasil dibuat!", f"Kode pesanan: {id_transaksi}", "Isinya:"]
        for alat, qty, sub in item_alat:
            baris.append(f"- {alat['nama_alat']} ({qty} buah x {durasi_hari} hari): Rp{sub:,.0f}")
        baris.append(f"Total bayar: Rp{total_biaya:,.0f}.")
        baris.append("Langkah berikutnya: bayar di menu Bayar Pesanan.")
        return True, "\n".join(baris)

    @staticmethod
    def lihat_tagihan(id_user):
        """Daftar tagihan user + ringkasan isi (untuk form bayar)."""
        hasil = []
        for t in TransaksiModel.lihatTagihanUser(id_user):
            isi = []
            for d in TransaksiModel.lihatDetail(t['id_transaksi']):
                isi.append(d['nama_studio'] if d['id_studio'] else f"{d['nama_alat']} x{d['jumlah']}")
            t['ringkasan'] = ', '.join(isi) or '-'
            hasil.append(t)
        return hasil

    @staticmethod
    def lihat_pesanan_saya(id_user):
        """Semua pesanan milik sendiri + ringkasan isi (aktif & riwayat, read-only)."""
        try:
            hasil = []
            for t in TransaksiModel.lihatRiwayatUser(id_user):
                isi = []
                for d in TransaksiModel.lihatDetail(t['id_transaksi']):
                    isi.append(d['nama_studio'] if d['id_studio'] else f"{d['nama_alat']} x{d['jumlah']}")
                t['ringkasan'] = ', '.join(isi) or '-'
                hasil.append(t)
            return hasil
        except (ValueError, TypeError, AttributeError):
            return []

    @staticmethod
    def lihat_tagihan_denda(id_user):
        """Tagihan denda user (Selesai + denda>0) + ringkasan isi."""
        hasil = []
        for t in TransaksiModel.lihatTagihanDendaUser(id_user):
            isi = []
            for d in TransaksiModel.lihatDetail(t['id_transaksi']):
                isi.append(d['nama_studio'] if d['id_studio'] else f"{d['nama_alat']} x{d['jumlah']}")
            t['ringkasan'] = ', '.join(isi) or '-'
            hasil.append(t)
        return hasil

    @staticmethod
    def _jam_db_ke_str(nilai):
        """timedelta/time/'HH:MM:SS' DB -> 'HH:MM' untuk cekJadwal. None -> None."""
        if nilai is None:
            return None
        try:
            if hasattr(nilai, 'total_seconds'):
                mnt = int(nilai.total_seconds() // 60)
                return "%02d:%02d" % (mnt // 60, mnt % 60)
            if hasattr(nilai, 'hour'):
                return "%02d:%02d" % (nilai.hour, nilai.minute)
            p = str(nilai).strip().split(':')
            return "%02d:%02d" % (int(p[0].split(',')[-1].strip().split()[-1]), int(p[1]))
        except (ValueError, TypeError, IndexError, AttributeError):
            return None

    @staticmethod
    def _slot_masih_kosong(id_transaksi):
        """Cek ulang slot studio transaksi Pending (dipakai saat verifikasi Diterima).

        Kembalikan (True, '') bila kosong / (False, pesan) bila direbut Lunas lain.
        """
        trx = TransaksiModel.getById(id_transaksi)
        if not trx:
            return False, f"Transaksi ID {id_transaksi} tidak ditemukan."
        tgl_s = trx['tgl_sewa'].strftime("%Y-%m-%d") if hasattr(trx['tgl_sewa'], 'strftime') else str(trx['tgl_sewa'])
        tgl_k = trx['tgl_kembali_rencana'].strftime("%Y-%m-%d") if hasattr(trx['tgl_kembali_rencana'], 'strftime') else str(trx['tgl_kembali_rencana'])
        for d in TransaksiModel.lihatDetail(id_transaksi):
            if not d.get('id_studio'):
                continue
            mulai = TransaksiController._jam_db_ke_str(d.get('jam_mulai'))
            selesai = TransaksiController._jam_db_ke_str(d.get('jam_selesai'))
            if mulai and selesai:
                bebas = StudioModel.cekJadwal(d['id_studio'], tgl_s, tgl_k, mulai, selesai)
            else:
                bebas = StudioModel.cekJadwal(d['id_studio'], tgl_s, tgl_k)
            if not bebas:
                return False, (
                    f"Slot studio '{d.get('nama_studio')}' sudah direbut booking Lunas lain. "
                    "Pembayaran tetap Menunggu — Tolak agar transaksi Batal."
                )
        return True, ""

    @staticmethod
    def proses_upload_bayar(id_user, id_transaksi, metode, bukti=None):
        """Catat pembayaran: jumlah diambil otomatis dari total transaksi / denda.

        - Sewa (Pending): jumlah = total_biaya.
        - Denda (Selesai + denda>0): jumlah = denda.
        - Tunai (cash di lokasi): tanpa foto, bukti boleh kosong/None -> disimpan NULL.
        - Transfer: wajib ada nama file bukti (contoh: bayar.jpg).
        Mencegah duplikat & transaksi milik orang lain.
        """
        try:
            id_transaksi = int(str(id_transaksi).strip())
        except (ValueError, AttributeError):
            return False, "ID Transaksi harus angka."
        metode = str(metode).strip().capitalize()
        if metode not in TransaksiController.METODE_BAYAR_VALID:
            return False, "Metode harus Tunai atau Transfer."
        bukti_bersih = str(bukti or '').strip() or None
        if metode == 'Transfer' and not bukti_bersih:
            return False, "Transfer wajib ada foto bukti (contoh: bayar.jpg)."

        trx = TransaksiModel.getById(id_transaksi)
        if not trx:
            return False, f"Transaksi ID {id_transaksi} tidak ditemukan."
        if trx['id_user'] != id_user:
            return False, "Transaksi ini bukan milik akun Anda."
        status_trx = trx['status_transaksi']
        bayar_denda = False
        if status_trx == 'Pending':
            nominal = float(trx['total_biaya'])
        elif status_trx == 'Selesai' and float(trx.get('denda') or 0) > 0:
            nominal = float(trx['denda'])
            bayar_denda = True
        else:
            return False, (
                f"Transaksi ID {id_transaksi} statusnya '{status_trx}'. "
                "Yang bisa dibayar: sewa 'Pending' atau denda 'Selesai'."
            )
        sudah = PembayaranModel.getByTransaksi(id_transaksi)
        if sudah and (sudah['status_konfirmasi'] == 'Menunggu'
                      or (not bayar_denda and sudah['status_konfirmasi'] == 'Diterima')):
            return False, (
                f"Transaksi ID {id_transaksi} sudah ada pembayaran "
                f"(status: {sudah['status_konfirmasi']}). Menunggu verifikasi operator."
            )

        ok = PembayaranModel.tambahPembayaran(
            id_transaksi, metode, bukti_bersih, nominal
        )
        if ok:
            jenis = f"Denda Rp{nominal:,.0f}" if bayar_denda else f"Rp{nominal:,.0f}"
            if metode == 'Tunai':
                return True, (
                    f"Pembayaran Tunai {jenis} tercatat! "
                    "Bayar cash di lokasi & tunggu operator memverifikasi."
                )
            return True, (
                f"Bukti bayar {jenis} terkirim! "
                "Tunggu operator memeriksa pembayaranmu."
            )
        return False, "Gagal mengunggah pembayaran (database)."

    @staticmethod
    def konfirmasi_pembayaran_transaksi(id_transaksi, id_pembayaran, status_pembayaran):
        """Operator mengonfirmasi pembayaran dan memperbarui status transaksi.

        Sewa (Pending): Diterima -> Lunas (cek ulang slot studio dulu),
        Ditolak -> Batal (buat pesanan baru di menu Sewa).
        Denda (Selesai): Diterima -> Tuntas, Ditolak -> tetap Selesai.
        """
        try:
            id_transaksi = int(str(id_transaksi).strip())
            id_pembayaran = int(str(id_pembayaran).strip())
        except (ValueError, AttributeError):
            return False, "ID Transaksi dan ID Pembayaran harus angka."
        if status_pembayaran not in ('Diterima', 'Ditolak'):
            return False, "Status harus Diterima atau Ditolak."

        bayar = PembayaranModel.getById(id_pembayaran)
        if not bayar:
            return False, f"Pembayaran ID {id_pembayaran} tidak ditemukan."
        if bayar['id_transaksi'] != id_transaksi:
            return False, (
                f"Pembayaran ID {id_pembayaran} milik transaksi {bayar['id_transaksi']}, "
                f"bukan {id_transaksi}. Cek kembali ID-nya."
            )
        if bayar['status_konfirmasi'] != 'Menunggu':
            return False, (
                f"Pembayaran ID {id_pembayaran} sudah '{bayar['status_konfirmasi']}', "
                "tidak bisa diverifikasi ulang."
            )

        trx = TransaksiModel.getById(id_transaksi)
        if not trx:
            return False, f"Transaksi ID {id_transaksi} tidak ditemukan."
        status_trx = trx['status_transaksi']
        bayar_denda = (status_trx == 'Selesai' and float(trx.get('denda') or 0) > 0)
        if status_trx not in ('Pending',) and not bayar_denda:
            return False, (
                f"Transaksi ID {id_transaksi} statusnya '{status_trx}'. "
                "Yang bisa diverifikasi: sewa 'Pending' atau denda 'Selesai'."
            )

        if status_pembayaran == 'Diterima' and status_trx == 'Pending':
            # Pending tidak mengunci slot: pastikan masih kosong sebelum Lunas
            bebas, pesan_slot = TransaksiController._slot_masih_kosong(id_transaksi)
            if not bebas:
                return False, pesan_slot

        verif_ok = PembayaranModel.verifikasi(id_pembayaran, status_pembayaran)
        if verif_ok:
            if bayar_denda:
                status_baru = 'Tuntas' if status_pembayaran == 'Diterima' else 'Selesai'
            else:
                # Sesuai ENUM transaksi: Pending, Lunas, Selesai, Batal, Tuntas
                status_baru = 'Lunas' if status_pembayaran == 'Diterima' else 'Batal'
            if TransaksiModel.ubahStatus(id_transaksi, status_baru):
                akhir = f" Status transaksi {id_transaksi} menjadi {status_baru}."
                if not bayar_denda and status_pembayaran == 'Ditolak':
                    akhir += " Silakan buat pesanan baru di menu Sewa."
                if bayar_denda and status_pembayaran == 'Ditolak':
                    akhir += " Denda belum lunas, silakan bayar ulang."
                return True, f"Pembayaran ID {id_pembayaran} {status_pembayaran}.{akhir}"
            # Transaksi gagal diubah: kembalikan pembayaran ke Menunggu agar konsisten
            PembayaranModel.verifikasi(id_pembayaran, 'Menunggu')
            return False, "Gagal memperbarui status transaksi. Verifikasi dibatalkan."
        return False, "Gagal memverifikasi pembayaran. Cek ID Pembayaran."

    @staticmethod
    def lihat_rincian(id_transaksi):
        """Rincian item satu transaksi (untuk layar operator)."""
        try:
            return TransaksiModel.lihatDetail(int(str(id_transaksi).strip()))
        except (ValueError, AttributeError):
            return []

    @staticmethod
    def lihat_pending():
        """Untuk menu operator: pesanan Pending / menunggu verifikasi."""
        return TransaksiModel.lihatPending()

    @staticmethod
    def lihat_riwayat():
        """Untuk menu operator: riwayat Selesai / Lunas / Batal / Tuntas."""
        return TransaksiModel.lihatRiwayat()
