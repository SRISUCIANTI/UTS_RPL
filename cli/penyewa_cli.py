from datetime import date, timedelta
from controllers.inventaris_controller import InventarisController
from controllers.transaksi_controller import TransaksiController

def _pilih_studio():
    """Tampilkan studio bernomor, kembalikan id_studio (angka) atau None.

    Hanya Tersedia yang bisa dipilih. Dibooking = tutup full sementara
    oleh operator, Maintenance = perawatan. Jadwal per-jam dicek lagi
    saat pesan (beda jam di tanggal sama tetap boleh).
    """
    studios = InventarisController.lihat_semua_studio()
    if not studios:
        print("Belum ada data studio.")
        return None
    while True:
        print("Langkah 1 - Pilih studio:")
        for i, s in enumerate(studios, start=1):
            print(f"  {i}. {s['nama_studio']} | Rp{s['harga_per_jam']:,.0f} tiap jam | {s['status_ketersediaan']}")
        pilih = input(f"Pilih (1-{len(studios)}, Enter=batal): ").strip()
        if not pilih:
            return None
        if not pilih.isdigit() or not 1 <= int(pilih) <= len(studios):
            print("[!] Pilihan tidak valid.")
            continue
        studio = studios[int(pilih) - 1]
        if studio['status_ketersediaan'] == 'Maintenance':
            print(f"[!] {studio['nama_studio']} tutup (perawatan), pilih yang lain.")
            continue
        if studio['status_ketersediaan'] == 'Dibooking':
            print(f"[!] {studio['nama_studio']} tutup sementara oleh operator. Hubungi operator untuk info buka.")
            continue
        return studio['id_studio']

def _input_tanggal_sewa():
    """Tanggal sewa: cepat (hari ini) atau ketik sendiri. Kembalikan string YYYY-MM-DD / None."""
    print("1. Hari ini (%s) | 2. Ketik sendiri" % date.today())
    pilih = input("Pilih (1/2, Enter=batal): ").strip()
    if not pilih:
        return None
    if pilih == '1':
        return str(date.today())
    if pilih == '2':
        return input("Ketik tanggalnya (contoh: 2026-12-25): ").strip()
    print("[!] Pilihan tidak valid.")
    return None

def _input_tanggal_kembali(tgl_sewa):
    """Rencana kembali: Besok/Lusa/3 hari dari sewa atau ketik sendiri. Kembalikan string / None."""
    print("  1. Besok (1 hari) | 2. Lusa (2 hari) | 3. 3 hari lagi | 4. Ketik sendiri")
    pilih = input("Pilih (1-4, Enter=batal): ").strip()
    if not pilih:
        return None
    if pilih in ('1', '2', '3'):
        try:
            d = date.fromisoformat(tgl_sewa)
        except ValueError:
            print("[!] Tanggal sewa tidak valid.")
            return None
        return str(d + timedelta(days=int(pilih)))
    if pilih == '4':
        return input("Ketik tanggalnya (contoh: 2026-12-25): ").strip()
    print("[!] Pilihan tidak valid.")
    return None

def _pilih_alat(terpilih):
    """Tampilkan katalog alat bernomor, kembalikan (id_alat, qty, nama) atau None (= selesai).

    terpilih: list (nama, qty) yang sudah dipilih, ditampilkan sebagai pengingat.
    Kembalikan 'ulang' bila input salah (minta pilih lagi).
    """
    alats = InventarisController.lihat_semua_alat()
    if not alats:
        print("Belum ada data alat.")
        return None
    print("Pilih alat yang mau disewa:")
    for i, a in enumerate(alats, start=1):
        print(f"  {i}. {a['nama_alat']} | Rp{a['harga_per_hari']:,.0f} per hari | Sisa {a['stok']}")
    if terpilih:
        print("Keranjang: " + ", ".join(f"{n} x{q}" for n, q in terpilih))
    pilih = input(f"Pilih (1-{len(alats)}, Enter=selesai): ").strip()
    if not pilih:
        return None
    if not pilih.isdigit() or not 1 <= int(pilih) <= len(alats):
        print("[!] Pilihan tidak valid.")
        return 'ulang'
    alat = alats[int(pilih) - 1]
    qty_in = input(f"Mau sewa berapa '{alat['nama_alat']}'? (sisa {alat['stok']}): ").strip()
    if not qty_in.isdigit() or int(qty_in) <= 0:
        print("[!] Jumlah harus angka lebih dari 0.")
        return 'ulang'
    print(f"Masuk keranjang: {alat['nama_alat']} x{qty_in}.")
    return (alat['id_alat'], int(qty_in), alat['nama_alat'])

def menu_penyewa(user):
    while True:
        print(f"\n======================================")
        print(f"  DASHBOARD PENYEWA: {user['nama_lengkap'].upper()}")
        print("======================================")
        print("1. Lihat Alat Lukis")
        print("2. Lihat Studio")
        print("3. Sewa Studio")
        print("4. Sewa Alat")
        print("5. Bayar Pesanan")
        print("6. Pesanan & Riwayat Saya")
        print("0. Keluar")
        pilihan = input("Pilih menu (0-6): ")

        if pilihan == '1':
            alats = InventarisController.lihat_semua_alat()
            print("\n--- ALAT LUKIS ---")
            if not alats:
                print("Belum ada data alat.")
            for a in alats:
                baris = f"{a['nama_alat']} | Rp{a['harga_per_hari']:,.0f} per hari | Sisa {a['stok']}"
                if a.get('deskripsi'):
                    baris += f"\n    {a['deskripsi']}"
                print(baris)

        elif pilihan == '2':
            studios = InventarisController.lihat_semua_studio()
            print("\n--- STUDIO ---")
            if not studios:
                print("Belum ada data studio.")
            for s in studios:
                if s['status_ketersediaan'] == 'Tersedia':
                    kondisi = "Bisa disewa (cek jam kosong di bawah)"
                elif s['status_ketersediaan'] == 'Dibooking':
                    kondisi = "Penuh/tutup sementara hari ini (operator)"
                elif s['status_ketersediaan'] == 'Maintenance':
                    kondisi = "Tutup (perawatan)"
                else:
                    kondisi = f"Status: {s['status_ketersediaan']}"
                print(f"{s['nama_studio']} | Muatan {s['kapasitas']} orang | "
                      f"Rp{s['harga_per_jam']:,.0f} tiap jam | {kondisi}")
                if s.get('fasilitas'):
                    print(f"    Isi studio: {s['fasilitas']}")
                for j in InventarisController.jadwal_studio(s['id_studio']):
                    print(f"    Sudah dibooking: {j}")

        elif pilihan == '3':
            print("\n--- SEWA STUDIO ---")
            id_studio = _pilih_studio()
            if id_studio is None:
                continue
            print("    (Alat bertuliskan 'Gratis dipakai' boleh dipakai tanpa bayar.)")
            print("Langkah 2 - Kapan mau pakai?")
            tgl_sewa = _input_tanggal_sewa()
            if not tgl_sewa:
                continue
            print("Langkah 3 - Mulai jam berapa? (0-21, contoh: 9 untuk 09.00, tutup 22.00)")
            from datetime import datetime as _dt
            print(f"    (Sekarang jam {_dt.now().strftime('%H.%M')}. Bila pakai hari ini, pilih jam setelah itu.)")
            jam_mulai = input("Jam mulai: ").strip()
            durasi = input("Berapa jam? Contoh: 2 : ").strip()

            ok, msg = TransaksiController.proses_pesan_studio(
                user['id_user'], id_studio, tgl_sewa, jam_mulai, durasi
            )
            print(f"\n[{'SUCCESS' if ok else 'ERROR'}] {msg}")

        elif pilihan == '4':
            print("\n--- SEWA ALAT ---")
            print("Langkah 1 - Kapan mulai sewanya?")
            tgl_sewa = _input_tanggal_sewa()
            if not tgl_sewa:
                continue
            print("Langkah 2 - Pilih alatnya:")
            daftar_alat = []
            dipilih_nama = []
            while True:
                hasil = _pilih_alat(dipilih_nama)
                if hasil is None:
                    break
                if hasil == 'ulang':
                    continue
                aid, qty, nama = hasil
                daftar_alat.append((aid, qty))
                dipilih_nama.append((nama, qty))
                lagi = input("Tambah alat lain? 1. Ya | 2. Tidak, lanjut: ").strip()
                if lagi != '1':
                    break
            if not daftar_alat:
                print("[!] Belum ada alat dipilih.")
                continue
            print("Langkah 3 - Alatnya mau dikembalikan kapan?")
            tgl_kembali = _input_tanggal_kembali(tgl_sewa)
            if not tgl_kembali:
                continue

            ok, msg = TransaksiController.proses_pesan_alat(
                user['id_user'], tgl_sewa, tgl_kembali, daftar_alat
            )
            print(f"\n[{'SUCCESS' if ok else 'ERROR'}] {msg}")

        elif pilihan == '5':
            print("\n--- BAYAR PESANAN ---")
            tagihan = TransaksiController.lihat_tagihan(user['id_user'])
            denda = TransaksiController.lihat_tagihan_denda(user['id_user'])
            if not tagihan and not denda:
                print("Tidak ada pesanan/tagihan yang menunggu bayar.")
                continue
            semua = ([(t, False) for t in tagihan] + [(t, True) for t in denda])
            print("Pesanan yang belum dibayar:")
            for i, (t, is_denda) in enumerate(semua, start=1):
                nominal = float(t.get('denda') or 0) if is_denda else float(t['total_biaya'])
                label = "DENDA" if is_denda else t.get('ringkasan')
                print(f"  {i}. Kode {t['id_transaksi']} | {label} | "
                      f"Tanggal {t['tgl_sewa']} | Total Rp{nominal:,.0f}")
            pilih = input(f"Pilih (1-{len(semua)}, Enter=batal): ").strip()
            if not pilih:
                continue
            if not pilih.isdigit() or not 1 <= int(pilih) <= len(semua):
                print("[!] Pilihan tidak valid.")
                continue
            t_terpilih, is_denda = semua[int(pilih) - 1]
            id_tx = t_terpilih['id_transaksi']

            print("Bayar lewat: 1. Tunai (cash di lokasi, tanpa foto) | 2. Transfer (wajib foto bukti)")
            m = input("Pilih (1/2, Enter=batal): ").strip()
            if not m:
                continue
            if m not in ('1', '2'):
                print("[!] Pilihan tidak valid.")
                continue
            if m == '1':
                ok, msg = TransaksiController.proses_upload_bayar(
                    user['id_user'], id_tx, 'Tunai', None
                )
            else:
                bukti = input("Nama file foto bukti bayar (contoh: bayar.jpg, Enter=batal): ").strip()
                if not bukti:
                    continue
                ok, msg = TransaksiController.proses_upload_bayar(
                    user['id_user'], id_tx, 'Transfer', bukti
                )
            print(f"\n[{'SUCCESS' if ok else 'ERROR'}] {msg}")

        elif pilihan == '6':
            print("\n--- PESANAN & RIWAYAT SAYA ---")
            riwayat = TransaksiController.lihat_pesanan_saya(user['id_user'])
            if not riwayat:
                print("Belum ada pesanan.")
                continue
            for i, t in enumerate(riwayat, start=1):
                metode = t.get('metode_bayar') or '-'
                bayar = t.get('status_pembayaran') or '-'
                denda = float(t.get('denda') or 0)
                print(f"  {i}. Kode {t['id_transaksi']} | {t.get('ringkasan') or '-'} | "
                      f"{t['tgl_sewa']} -> {t['tgl_kembali_rencana']} | "
                      f"Total Rp{float(t['total_biaya']):,.0f} | Denda Rp{denda:,.0f} | "
                      f"{t['status_transaksi']} | {metode} / {bayar}")
            pilih = input(f"Pilih nomor untuk rincian (1-{len(riwayat)}, Enter=kembali): ").strip()
            if not pilih:
                continue
            if not pilih.isdigit() or not 1 <= int(pilih) <= len(riwayat):
                print("[!] Pilihan tidak valid.")
                continue
            t = riwayat[int(pilih) - 1]
            print(f"\nKode {t['id_transaksi']} | {t.get('ringkasan') or '-'}")
            print(f"Tgl: {t['tgl_sewa']} -> {t['tgl_kembali_rencana']} | "
                  f"Kembali aktual: {t.get('tgl_kembali_aktual') or '-'}")
            metode = t.get('metode_bayar') or '-'
            bukti = t.get('bukti_bayar') or '-'
            if metode == 'Tunai':
                print(f"Bayar: Tunai (cash di lokasi, tanpa foto) | Status: {t.get('status_pembayaran') or '-'}")
            elif metode == '-':
                print("Bayar: belum bayar (menu 5 untuk bayar).")
            else:
                print(f"Bayar: {metode} | Bukti: {bukti} | Status: {t.get('status_pembayaran') or '-'}")
            rincian = TransaksiController.lihat_rincian(t['id_transaksi'])
            if not rincian:
                print("  (tidak ada rincian item)")
                continue
            print("  Rincian item:")
            for d in rincian:
                if d['id_studio']:
                    jam = ""
                    if d.get('jam_mulai') is not None and d.get('jam_selesai') is not None:
                        jam = f" jam {InventarisController.tampil_jam(d['jam_mulai'])}-{InventarisController.tampil_jam(d['jam_selesai'])}"
                    print(f"  - Studio: {d['nama_studio']} | {d['jumlah']} jam{jam} | Rp{float(d['subtotal']):,.0f}")
                else:
                    print(f"  - {d['nama_alat']} x{d['jumlah']} | Rp{float(d['subtotal']):,.0f}")

        elif pilihan == '0':
            break
