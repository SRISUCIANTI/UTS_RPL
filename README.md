# 🎨 ArtStudio-Rent
**Sistem Informasi Sewa Alat Lukis & Studio Kreatif**

Aplikasi berbasis desktop (*Python CustomTkinter*) dengan arsitektur **Model-View-Controller (MVC)** dan basis data **MySQL** untuk mengotomatisasi inventaris alat seni, reservasi jadwal ruang studio secara *real-time*, pencatatan transaksi sewa, verifikasi pembayaran manual, serta kalkulasi denda keterlambatan otomatis.

Proyek ini disusun untuk memenuhi Ujian Tengah Semester (UTS) mata kuliah **Praktikum Rekayasa Perangkat Lunak**, Program Studi S1 Sistem Informasi, Universitas Tadulako[cite: 1].

---

## 👥 Tim Pengembang (Kelompok 5 - Kelas B)
| Nama Anggota | NIM | Peran Utama |
| :--- | :--- | :--- |
| **M. Setiyawan** | F5212520060 | Ketua Kelompok / Owner |
| **Bimo Prakoso B** | F5212520070 | Staf / Operator[cite: 1, 4] |
| **Nabhita Akhilla** | F5212520057 | Penyewa / Pelanggan[cite: 1, 4] |
| **Ananda Muthi’ah Z** | F5212520059 | Penyewa / Pelanggan[cite: 1, 4] |
| **Sri Sucianti** | F5212520062 | Penyewa / Pelanggan[cite: 1, 4] |
| **Fatih Ariqah** | F5212520071 | Penyewa / Pelanggan[cite: 1, 4] |

---

## ✨ Fitur Utama Berdasarkan Peran (Role)
1. **Penyewa / Pelanggan:**
   * Registrasi dan *login* akun[cite: 1].
   * Melihat katalog ketersediaan alat lukis dan jadwal slot ruang studio secara *real-time*[cite: 1].
   * Membuat pesanan sewa alat/studio dan memantau status pembayaran[cite: 1].
2. **Staf / Operator:**
   * Mengelola data master inventaris alat lukis dan ruang studio (CRUD)[cite: 1].
   * Memverifikasi konfirmasi pembayaran manual (*Pending* menjadi *Lunas*)[cite: 1].
   * Memproses pengembalian barang, validasi kondisi barang, dan kalkulasi denda keterlambatan otomatis[cite: 1].
   * Melihat riwayat transaksi penyewaan[cite: 1].
3. **Pemilik Studio (Owner):**
   * Melihat ringkasan total pendapatan lunas pada *Dashboard Eksekutif*[cite: 1].
   * Mengakses dan mencetak/ekspor rekapitulasi laporan pendapatan bulanan[cite: 1].

---

## 🛠️ Teknologi yang Digunakan
* **Bahasa Pemrograman:** Python 3.14[cite: 3]
* **Antarmuka (GUI):** CustomTkinter & Tkinter (`ttk.Treeview`)[cite: 4]
* **Basis Data:** MySQL (via Laragon / phpMyAdmin)[cite: 1, 4]
* **Arsitektur:** Model-View-Controller (MVC)[cite: 1]

---

## 📂 Struktur Direktori Proyek
```text
UTS_RPL/
├── config/             # Konfigurasi koneksi database MySQL (database.py)[cite: 1]
├── controllers/        # Pengendali alur logika (auth, inventaris, transaksi, pengembalian, laporan)[cite: 1]
├── models/             # Interaksi query CRUD ke database MySQL[cite: 1]
├── views/
│   ├── cli/            # Antarmuka berbasis terminal (CLI)[cite: 1]
│   └── gui/            # Antarmuka grafis desktop (login_gui, penyewa_gui, operator_gui, owner_gui)[cite: 1]
├── main.py             # Entry point utama aplikasi[cite: 1]
└── requirements.txt    # Daftar pustaka/dependensi Python[cite: 1]