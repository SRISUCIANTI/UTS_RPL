from controllers.inventaris_controller import InventarisController
from controllers.transaksi_controller import TransaksiController
from controllers.pengembalian_controller import PengembalianController

def _tampil_daftar(transaksis, judul):
    print(f"\n--- {judul} ---")
    if not transaksis:
        print("Tidak ada data.")
        return
    for t in transaksis:
        id_bayar = t.get('id_pembayaran') or '-'
        metode = t.get('metode_bayar') or '-'
        bukti = t.get('bukti_bayar') or '-'
        bukti_txt = '' if metode == 'Tunai' else f" | Bukti:{bukti}"
        print(
            f"ID-Trx:{t['id_transaksi']} | ID-Bayar:{id_bayar} | Penyewa:{t['username']} ({t['nama_lengkap']}) | "
            f"Sewa:{t['tgl_sewa']} -> Rencana Kembali:{t['tgl_kembali_rencana']} | "
            f"Total:Rp{t['total_biaya']:,.0f} | Denda:Rp{(t['denda'] or 0):,.0f} | "
            f"Status:{t['status_transaksi']} | {metode}{bukti_txt} | Bayar:{t.get('status_pembayaran') or '-'}"
        )

def _tampil_rincian(id_transaksi):
    rincian = TransaksiController.lihat_rincian(id_transaksi)
    if not rincian:
        print("  (tidak ada rincian item)")
        return
    print("  Rincian item:")
    for d in rincian:
        if d['id_studio']:
            jam = ""
            if d.get('jam_mulai') is not None and d.get('jam_selesai') is not None:
                jam = f" jam {InventarisController.tampil_jam(d['jam_mulai'])}-{InventarisController.tampil_jam(d['jam_selesai'])}"
            print(f"  - Studio: {d['nama_studio']} | {d['jumlah']} jam{jam} | Rp{float(d['subtotal']):,.0f}")
        else:
            print(f"  - {d['nama_alat']} x{d['jumlah']} | Rp{float(d['subtotal']):,.0f}")

def _pilih_nomor(jumlah, teks="Pilih"):
    """Baca pilihan bernomor 1..jumlah. Kembalikan int / None (batal/tidak valid)."""
    pilih = input(f"{teks} (1-{jumlah}, Enter=batal): ").strip()
    if not pilih:
        return None
    if not pilih.isdigit() or not 1 <= int(pilih) <= jumlah:
        print("[!] Pilihan tidak valid.")
        return None
    return int(pilih)

def _input_angka(label, tipe):
    """Baca angka dari user. Kembalikan nilai / None bila bukan angka."""
    teks = input(label).strip().replace('.', '').replace(',', '')
    try:
        return tipe(teks)
    except ValueError:
        print(f"[!] {label.strip(' :')} harus angka.")
        return None

def parse_nominal(teks):
    """Parse nominal gaya Indonesia: '50.000' -> 50000, '50.000,50' -> 50000.5.

    Kembalikan float / None bila bukan angka.
    """
    teks = str(teks or '').strip().replace(' ', '').replace('Rp', '').replace('rp', '')
    if not teks:
        return None
    try:
        if ',' in teks:
            depan, belakang = teks.rsplit(',', 1)
            return float(depan.replace('.', '') + '.' + belakang.replace('.', ''))
        return float(teks.replace('.', ''))
    except ValueError:
        return None

def _input_tarif(label):
    """Baca tarif dari user (terima '50000' / '50.000' / '50.000,50')."""
    nilai = parse_nominal(input(label))
    if nilai is None:
        print(f"[!] {label.strip(' :')} harus angka.")
        return None
    return nilai

def menu_operator(user):
    while True:
        print(f"\n======================================")
        print(f"  DASHBOARD OPERATOR: {user['nama_lengkap'].upper()}")
        print("======================================")
        print("1. Tambah Data Alat Lukis")
        print("2. Tambah Data Studio")
        print("3. Verifikasi Pembayaran Transaksi")
        print("4. Proses Pengembalian & Denda")
        print("5. Lihat Daftar Pesanan Pending")
        print("6. Lihat Riwayat Transaksi (Selesai/Lunas/Batal/Tuntas)")
        print("7. Atur Status Ketersediaan Studio")
        print("8. Edit / Hapus Data Studio")
        print("0. Logout")
        pilihan = input("Pilih menu (0-8): ")

        if pilihan == '1':
            print("\n--- TAMBAH ALAT ---")
            nama = input("Nama Alat        : ").strip()
            deskripsi = input("Deskripsi        : ").strip()
            stok = _input_angka("Stok             : ", int)
            if stok is None:
                continue
            tarif = _input_tarif("Tarif Sewa/hari  : ")
            if tarif is None:
                continue
            
            ok, msg = InventarisController.kelola_alat('tambah', nama_alat=nama, kategori=deskripsi, stok=stok, tarif_sewa=tarif)
            print(f"\n[{'SUCCESS' if ok else 'ERROR'}] {msg}")

        elif pilihan == '2':
            print("\n--- TAMBAH STUDIO ---")
            nama = input("Nama Studio      : ").strip()
            kap = _input_angka("Kapasitas        : ", int)
            if kap is None:
                continue
            tarif = _input_tarif("Tarif Sewa/jam   : ")
            if tarif is None:
                continue
            fasilitas = input("Fasilitas (opsional): ").strip() or None
            
            ok, msg = InventarisController.kelola_studio('tambah', nama_studio=nama, kapasitas=kap, tarif_sewa=tarif, fasilitas=fasilitas)
            print(f"\n[{'SUCCESS' if ok else 'ERROR'}] {msg}")

        elif pilihan == '3':
            print("\n--- VERIFIKASI PEMBAYARAN ---")
            antre = TransaksiController.lihat_pending()
            if not antre:
                print("Tidak ada antrean menunggu verifikasi.")
                continue
            print("Antrean:")
            for i, t in enumerate(antre, start=1):
                metode = t.get('metode_bayar') or '-'
                print(f"  {i}. ID-Trx {t['id_transaksi']} | ID-Bayar {t.get('id_pembayaran') or '-'} | "
                      f"{t['username']} ({t['nama_lengkap']}) | Rp{t['total_biaya']:,.0f} | "
                      f"{metode} | Bayar: {t.get('status_pembayaran') or '-'}")
            nomor = _pilih_nomor(len(antre))
            if nomor is None:
                continue
            pilih = antre[nomor - 1]
            id_tx, id_bayar = pilih['id_transaksi'], pilih.get('id_pembayaran')
            _tampil_rincian(id_tx)
            if not id_bayar:
                print("[INFO] Transaksi ini belum ada pembayaran. Minta penyewa upload bukti dulu.")
                continue
            metode = pilih.get('metode_bayar') or '-'
            bukti = pilih.get('bukti_bayar') or '-'
            if metode == 'Tunai':
                print(f"Metode: Tunai (cash di lokasi, tanpa foto). Bukti: {bukti}")
            else:
                print(f"Metode: {metode} | Bukti: {bukti}")
            print("Status: 1. Diterima | 2. Ditolak")
            st = input("Pilih (1/2): ").strip()
            if st not in ('1', '2'):
                print("[!] Pilihan tidak valid.")
                continue
            
            ok, msg = TransaksiController.konfirmasi_pembayaran_transaksi(
                id_tx, id_bayar, 'Diterima' if st == '1' else 'Ditolak')
            print(f"\n[{'SUCCESS' if ok else 'ERROR'}] {msg}")

        elif pilihan == '4':
            print("\n--- PROSES PENGEMBALIAN & DENDA ---")
            aktif = PengembalianController.lihat_belum_kembali()
            if not aktif:
                print("Tidak ada sewa aktif. Semua sudah dikembalikan.")
                continue
            print("Sewa aktif:")
            for i, t in enumerate(aktif, start=1):
                hari = t.get('estimasi_terlambat_hari', 0) or 0
                flag = f"TERLAMBAT {hari} hari" if hari > 0 else "tepat waktu"
                print(f"  {i}. ID-Trx {t['id_transaksi']} | {t['username']} ({t['nama_lengkap']}) | "
                      f"Kembali {t['tgl_kembali_rencana']} | {flag}")
            nomor = _pilih_nomor(len(aktif))
            if nomor is None:
                continue
            id_tx = aktif[nomor - 1]['id_transaksi']
            _tampil_rincian(id_tx)
            tgl_aktual = input("Tanggal Aktual Kembali (YYYY-MM-DD, Enter=hari ini): ").strip()

            ok, msg = PengembalianController.proses_kembali(id_tx, tgl_aktual)
            print(f"\n[{'SUCCESS' if ok else 'ERROR'}] {msg}")

        elif pilihan == '5':
            data = TransaksiController.lihat_pending()
            _tampil_daftar(data, "PESANAN PENDING / MENUNGGU VERIFIKASI")

        elif pilihan == '6':
            data = TransaksiController.lihat_riwayat()
            _tampil_daftar(data, "RIWAYAT TRANSAKSI")

        elif pilihan == '7':
            print("\n--- STATUS KETERSEDIAAN STUDIO ---")
            print("Tersedia = buka (booking per jam tetap dicek).")
            print("Dibooking = TUTUP FULL sementara oleh operator (blokir semua tanggal).")
            print("Maintenance = tutup perawatan.")
            studios = InventarisController.lihat_semua_studio()
            if not studios:
                print("Belum ada data studio.")
                continue
            tutup = [s for s in studios if s['status_ketersediaan'] != 'Tersedia']
            if tutup:
                daftar = ", ".join(f"{s['nama_studio']} ({s['status_ketersediaan']})" for s in tutup)
                print(f"[PERHATIAN] Masih TUTUP: {daftar}.")
                print("            Kembalikan ke Tersedia bila sudah buka lagi!")
            for i, s in enumerate(studios, start=1):
                hari_ini = InventarisController.jadwal_hari_ini(s['id_studio'])
                info_hari = ("Hari ini: " + ", ".join(hari_ini)) if hari_ini else "Hari ini: kosong"
                print(f"  {i}. {s['nama_studio']} | "
                      f"Tarif: Rp{s['harga_per_jam']:,.0f}/jam | Status: {s['status_ketersediaan']} | {info_hari}")
            nomor = _pilih_nomor(len(studios))
            if nomor is None:
                continue
            cur = studios[nomor - 1]
            id_studio = cur['id_studio']
            print(f"Dipilih: {cur['nama_studio']} (sekarang: {cur['status_ketersediaan']})")
            print("Status baru: 1. Buka (Tersedia) | 2. Tandai Full Hari Ini (Dibooking) | 3. Maintenance")
            pilih_status = input("Pilih (1/2/3, Enter=batal): ").strip()
            if not pilih_status:
                print("[BATAL] Kembali ke menu operator.")
                continue
            peta = {'1': 'Tersedia', '2': 'Dibooking', '3': 'Maintenance'}
            if pilih_status not in peta:
                print("[!] Pilihan tidak valid.")
                continue
            if peta[pilih_status] == 'Dibooking':
                yakin = input("Tandai FULL (tutup semua booking baru)? 1. Ya | Enter=batal: ").strip()
                if yakin != '1':
                    print("[BATAL] Tidak ada perubahan.")
                    continue

            ok, msg = InventarisController.atur_status_studio(id_studio, peta[pilih_status])
            print(f"\n[{'SUCCESS' if ok else 'ERROR'}] {msg}")

        elif pilihan == '8':
            print("\n--- EDIT / HAPUS DATA STUDIO ---")
            print("Ketik 0 / batal di mana saja untuk membatalkan.")
            studios = InventarisController.lihat_semua_studio()
            if not studios:
                print("Belum ada data studio.")
                continue
            for i, s in enumerate(studios, start=1):
                print(f"  {i}. {s['nama_studio']} | Kapasitas: {s['kapasitas']} | "
                      f"Tarif: Rp{s['harga_per_jam']:,.0f}/jam | Status: {s['status_ketersediaan']}")
            nomor = _pilih_nomor(len(studios), teks="Pilih nomor studio")
            if nomor is None:
                print("[BATAL] Kembali ke menu operator.")
                continue
            cur = studios[nomor - 1]
            id_studio = cur['id_studio']
            print(f"\nDipilih: {cur['nama_studio']} | Kapasitas: {cur['kapasitas']} | "
                  f"Tarif: Rp{float(cur['harga_per_jam']):,.0f}/jam | Fasilitas: {cur.get('fasilitas') or '-'}")
            print("Mau apa? 1. Edit | 2. Hapus | Enter=batal")
            aksi = input("Pilih (1/2): ").strip()
            if aksi == '':
                print("[BATAL] Kembali ke menu operator.")
                continue
            if aksi not in ('1', '2'):
                print("[!] Pilihan tidak valid.")
                continue

            if aksi == '2':
                print(f"\n[PERINGATAN] Yakin hapus '{cur['nama_studio']}'? Tidak bisa dibatalkan.")
                print("Studio yang pernah disewa / masih dibooking TIDAK bisa dihapus.")
                konfirm = input("Ketik HAPUS untuk konfirmasi (Enter=batal): ").strip()
                if konfirm != 'HAPUS':
                    print("[BATAL] Hapus dibatalkan, tidak ada data diubah.")
                    continue
                ok, msg = InventarisController.hapus_studio(int(id_studio))
                print(f"\n[{'SUCCESS' if ok else 'ERROR'}] {msg}")
                continue

            print("\n--- EDIT (Enter = pertahankan lama, ketik batal = tidak jadi) ---")

            nama_in = input(f"Nama [{cur['nama_studio']}] : ").strip()
            if nama_in.lower() in ('0', 'batal', 'cancel'):
                print("[BATAL] Edit dibatalkan, tidak ada data diubah.")
                continue
            nama = nama_in or cur['nama_studio']

            kap_in = input(f"Kapasitas [{cur['kapasitas']}] : ").strip()
            if kap_in.lower() in ('batal', 'cancel'):
                print("[BATAL] Edit dibatalkan, tidak ada data diubah.")
                continue
            tarif_in = input(f"Tarif/jam [{float(cur['harga_per_jam']):,.0f}] : ").strip()
            if tarif_in.lower() in ('batal', 'cancel'):
                print("[BATAL] Edit dibatalkan, tidak ada data diubah.")
                continue
            fas = input("Fasilitas (tulis ulang semua, Enter=tetap, ketik batal=tidak jadi): ").strip()
            if fas.lower() in ('batal', 'cancel'):
                print("[BATAL] Edit dibatalkan, tidak ada data diubah.")
                continue

            try:
                kap = int(kap_in) if kap_in else cur['kapasitas']
                tarif = parse_nominal(tarif_in) if tarif_in else float(cur['harga_per_jam'])
                if tarif is None:
                    raise ValueError
            except ValueError:
                print("[!] Kapasitas/tarif harus angka.")
                continue
            fasilitas_baru = (fas if fas else cur.get('fasilitas'))

            # Kalau tidak ada yang diubah -> batal otomatis, jangan panggil DB
            if (nama == cur['nama_studio'] and kap == cur['kapasitas']
                    and float(tarif) == float(cur['harga_per_jam'])
                    and fasilitas_baru == cur.get('fasilitas')):
                print("[BATAL] Tidak ada perubahan (semua Enter). Edit dibatalkan.")
                continue

            print(f"\nBaru  : {nama} | Kapasitas: {kap} | "
                  f"Tarif: Rp{float(tarif):,.0f}/jam | Fasilitas: {fasilitas_baru or '-'}")
            yakin = input("Simpan perubahan? 1. Ya, simpan | 2. Tidak, batal (Enter=batal): ").strip()
            if yakin != '1':
                print("[BATAL] Edit dibatalkan, tidak ada data diubah.")
                continue

            ok, msg = InventarisController.kelola_studio(
                'update', id_studio=int(id_studio), nama_studio=nama,
                kapasitas=kap, tarif_sewa=tarif,
                fasilitas=fasilitas_baru
            )
            print(f"\n[{'SUCCESS' if ok else 'ERROR'}] {msg}")

        elif pilihan == '0':
            break
