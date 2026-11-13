from controllers.laporan_controller import LaporanController

def _tampil(baris):
    if baris is None:
        print("\n[ERROR] Laporan gagal dibuat (input tidak valid / database).")
        return
    print()
    for b in baris:
        print(b)

def _cetak(nama_jenis, baris):
    if baris is None:
        print("\n[ERROR] Laporan gagal dibuat (input tidak valid / database).")
        return
    nama_file = LaporanController.simpan_txt(nama_jenis, baris)
    if nama_file:
        print(f"\n[SUCCESS] Laporan tersimpan: {nama_file}")
    else:
        print("\n[ERROR] Gagal menyimpan laporan ke file.")

def _minta_filter_riwayat():
    print("Filter status (Pending/Lunas/Selesai/Batal/Tuntas, Enter=semua)")
    return input("Status: ").strip() or None

def _minta_filter_bulan():
    print("Bulan format YYYY-MM (Enter=semua bulan)")
    return input("Bulan: ").strip() or None

def menu_owner(user):
    while True:
        print(f"\n======================================")
        print(f"     DASHBOARD OWNER: {user['nama_lengkap'].upper()}")
        print("======================================")
        print("1. Lihat Rekapitulasi Pendapatan")
        print("2. Lihat Riwayat Transaksi Sewa")
        print("3. Lihat Pendapatan Bulanan")
        print("4. Cetak Laporan ke File TXT")
        print("0. Logout")
        pilihan = input("Pilih menu (0-4): ")

        if pilihan == '1':
            _tampil(LaporanController.rekap_umum())

        elif pilihan == '2':
            _tampil(LaporanController.riwayat_transaksi(_minta_filter_riwayat()))

        elif pilihan == '3':
            _tampil(LaporanController.pendapatan_bulanan(_minta_filter_bulan()))

        elif pilihan == '4':
            print("\n--- CETAK LAPORAN ---")
            print("1. Rekapitulasi Pendapatan")
            print("2. Riwayat Transaksi Sewa")
            print("3. Pendapatan Bulanan")
            print("4. Semuanya")
            print("0. Batal")
            cetak = input("Cetak yang mana (0-4): ").strip()
            if cetak == '1':
                _cetak("rekap", LaporanController.rekap_umum())
            elif cetak == '2':
                _cetak("riwayat", LaporanController.riwayat_transaksi(_minta_filter_riwayat()))
            elif cetak == '3':
                _cetak("bulanan", LaporanController.pendapatan_bulanan(_minta_filter_bulan()))
            elif cetak == '4':
                _cetak("rekap", LaporanController.rekap_umum())
                _cetak("riwayat", LaporanController.riwayat_transaksi())
                _cetak("bulanan", LaporanController.pendapatan_bulanan())
            elif cetak == '0':
                pass
            else:
                print("[!] Pilihan tidak valid.")

        elif pilihan == '0':
            break
