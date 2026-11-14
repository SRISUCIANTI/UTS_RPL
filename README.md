# 🎨 ArtStudio-Rent
**Sistem Informasi Sewa Alat Lukis & Studio Kreatif**

Aplikasi berbasis desktop (*Python CustomTkinter*) dengan arsitektur **Model-View-Controller (MVC)** dan basis data **MySQL** untuk mengotomatisasi inventaris alat seni, reservasi jadwal ruang studio secara *real-time*, pencatatan transaksi sewa, verifikasi pembayaran manual, serta kalkulasi denda keterlambatan otomatis.

Proyek ini disusun untuk memenuhi Ujian Tengah Semester (UTS) dan Ujian Akhir Semester (UAS) mata kuliah **Praktikum Rekayasa Perangkat Lunak**, Program Studi S1 Sistem Informasi, Universitas Tadulako

---

## Tim Pengembang (Kelompok 5 - Kelas B)

| No. | Nama Anggota | NIM | Peran Utama |
| :-: | :--- | :---: | :--- |
| 1. | **Nabhita Akhilla** | F5212520057 | Requirements Analyst & Database Architect |
| 2. | **Ananda Muthi’ah Z** | F5212520059 | UI/UX & Frontend Designers (View) |
| 3. | **M. Setiyawan** | F5212520060 | UML & Class Designers |
| 4. | **Sri Sucianti** | F5212520062 | UI/UX & Frontend Designers (View) |
| 5. | **Bimo Prakoso B** | F5212520070 | System Analyst, Flow Designer & Backend |
| 6. | **Fatih Ariqah** | F5212520071 | UML & Class Designers |

---

## Fitur Utama Berdasarkan Peran (Role)
1. **Penyewa / Pelanggan:**
   * Registrasi dan *login* akun.
   * Melihat katalog ketersediaan alat lukis dan jadwal slot ruang studio secara *real-time*
   * Membuat pesanan sewa alat/studio dan memantau status pembayaran
2. **Staf / Operator:**
   * Mengelola data master inventaris alat lukis dan ruang studio (CRUD)
   * Memverifikasi konfirmasi pembayaran manual (*Pending* menjadi *Lunas*)
   * Memproses pengembalian barang, validasi kondisi barang, dan kalkulasi denda keterlambatan otomatis
   * Melihat riwayat transaksi penyewaan
3. **Pemilik Studio (Owner):**
   * Melihat ringkasan total pendapatan lunas pada *Dashboard Eksekutif*
   * Mengakses dan mencetak/ekspor rekapitulasi laporan pendapatan bulanan

---

## Teknologi yang Digunakan
* **Bahasa Pemrograman:** Python 3.14
* **Antarmuka (GUI):** CustomTkinter & Tkinter (`ttk.Treeview`)
* **Basis Data:** MySQL (via Laragon / phpMyAdmin)
* **Arsitektur:** Model-View-Controller (MVC)

---

## 📂Struktur Direktori Proyek
```text
UTS_RPL/
├── config/             # Konfigurasi koneksi database MySQL (database.py)
├── controllers/        # Pengendali alur logika (auth, inventaris, transaksi, pengembalian, laporan)
├── models/             # Interaksi query CRUD ke database MySQL
├── views/
│   ├── cli/            # Antarmuka berbasis terminal (CLI)
│   └── gui/            # Antarmuka grafis desktop (login_gui, penyewa_gui, operator_gui, owner_gui)
├── main.py             # Entry point utama aplikasi
└── requirements.txt    # Daftar pustaka/dependensi Python
