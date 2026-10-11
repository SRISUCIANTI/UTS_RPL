# ARTSTUDIO-RENT — Dokumentasi Program (untuk Verifikasi)

Program penyewaan studio dan alat lukis berbasis Python CLI dengan arsitektur
**MVC**, database MySQL `artstudio_rent`. Cara jalan: `python main.py`.

---

## 1. Struktur File

```text
artstudio-rent/
├── main.py                     # entry point, routing role, tangkap Ctrl+C/EOF
├── requirements.txt
├── Plan.md                     # file ini (dokumen + skenario UAT §7)
├── config/
│   └── database.py             # get_connection() -> MySQL localhost root artstudio_rent
├── models/
│   ├── user_model.py           # login (finally) + registrasi
│   ├── alat_model.py           # alat: lihatSemua, cekKetersediaan, kelolaData, ubahStok atomik
│   ├── studio_model.py         # studio + cekJadwal/lihatSemua/jadwalStudio (Lunas-only, realtime)
│   ├── transaksi_model.py      # transaksi + detail + tagihan sewa/denda + riwayat (Tuntas)
│   ├── pembayaran_model.py     # pembayaran: verifikasi, tambah, getById, getByTransaksi
│   ├── pengembalian_model.py   # hitungDenda, getTransaksi, lihatBelumKembali, prosesPengembalian
│   └── laporan_model.py        # rekapUmum, riwayat, pendapatanBulanan (denda hanya Tuntas)
├── controllers/
│   ├── auth_controller.py      # login/register + hash SHA-256
│   ├── inventaris_controller.py# alat/studio CRUD (stok>=0, kapasitas>0), status, tampil_jam 24.00-safe
│   ├── transaksi_controller.py # pesan (tutup 22, tolak masa lalu), bayar sewa/denda,
│   │                           # verifikasi anti-ganda + cek slot + Tuntas
│   ├── pengembalian_controller.py # estimasi denda + kembali (tolak aktual<sewa) + restore stok
│   └── laporan_controller.py   # format laporan + simpan TXT (filter Tuntas)
└── views/cli/
    ├── auth_cli.py             # login + registrasi tervalidasi
    ├── penyewa_cli.py          # menu 1-6: katalog, sewa studio/alat, bayar sewa+denda, riwayat sendiri
    ├── operator_cli.py         # menu 1-8 + parse_nominal Indonesia
    └── owner_cli.py            # menu 1-4 laporan + cetak TXT (filter Tuntas)
```

Semua file di atas aktif dipakai dan terakhir diselaraskan Tahap 1+2
(verifikasi anti-ganda, denda/`Tuntas`, `Pending` tak mengunci slot,
tutup 22.00, Tunai tanpa foto, jadwal realtime).

---

## 2. Skema Database (FIX — 6 tabel, tidak boleh tambah/kurang)

- `users(id_user, username, email, password, nama_lengkap, role, no_hp)`
  role: `Penyewa | Operator | Owner`
- `studio(id_studio, nama_studio, harga_per_jam, kapasitas, fasilitas,
  status_ketersediaan)` — status: `Tersedia | Dibooking | Maintenance`
- `alat(id_alat, nama_alat, harga_per_hari, stok, deskripsi)`
- `transaksi(id_transaksi, id_user, tgl_sewa, tgl_kembali_rencana,
  tgl_kembali_aktual, total_biaya, denda, status_transaksi)`
  status: `Pending | Lunas | Selesai | Batal | Tuntas` (`Tuntas` = Selesai + denda lunas)
- `detail_transaksi(id_detail, id_transaksi, id_alat NULL, id_studio NULL,
  jumlah, subtotal, jam_mulai TIME NULL, jam_selesai TIME NULL)` —
  tepat satu dari `id_alat`/`id_studio` terisi; jam hanya untuk studio
- `pembayaran(id_pembayaran, id_transaksi, tgl_bayar, metode_bayar,
  jumlah_bayar, bukti_bayar, status_konfirmasi)`
  metode: `Tunai | Transfer`; konfirmasi: `Menunggu | Diterima | Ditolak`

**Alat gratis bawaan studio** hanya berupa teks biasa di `fasilitas`
(contoh: `... AC, Wi-Fi. Gratis dipakai: Easel Stand Kayu Tinggi`).
Tidak ada tabel/mapping/penanda ID — ubah teksnya langsung di DB atau via
menu operator 8 (Edit Data Studio).

---

## 3. Aturan Bisnis (acuan pengecekan)

1. **Pemesanan dipisah**: menu Sewa Studio (per tanggal + jam) dan Sewa
   Alat (per stok) masing-masing satu transaksi; tidak ada pesan gabungan.
2. **Harga studio** = `harga_per_jam x durasi jam` (tarif otomatis dari DB).
   Jam mulai 0-21, jam selesai = mulai + durasi (maksimal 22.00 ikut
   jam tutup toko, tanpa lewat tengah malam); tanggal kembali otomatis
   = tanggal sewa. Tanggal masa lalu ditolak; bila sewa hari ini,
   jam mulai harus setelah jam sekarang (blok penuh per jam).
3. **Harga alat berbayar** = `harga_per_hari x jumlah x durasi hari`
   (durasi = selisih tanggal, sewa-kembali hari yang sama = 1 hari).
4. **Alat gratis**: sekadar info teks di `fasilitas` studio
   ("Gratis dipakai: ..."), bebas dipakai selama sewa. Tidak dicatat di
   transaksi, tidak memotong stok.
5. **Stok alat**: dicek lalu dikurangi saat pesan; dikembalikan utuh
   saat transaksi menjadi `Selesai`. Update pengurangan atomik
   (`stok >= 0`), tidak bisa minus.
6. **Ketersediaan studio**: tolak jika `Maintenance` (perawatan) atau
   `Dibooking` (tutup manual / full hari ini oleh operator), atau tanggal
   bersinggungan DAN jam bersinggungan dengan booking **Lunas**.
   Hanya `Lunas` yang mengunci slot (`Pending` tak-bayar tidak menahan;
   verifikasi `Diterima` cek ulang slot). Beda jam di tanggal sama = boleh. Baris lama tanpa
   jam dianggap memenuhi seharian. Kolom `status_ketersediaan`
   TIDAK diubah otomatis oleh pemesanan (operator mengembalikan
   `Dibooking -> Tersedia` manual besok, menu 7 menampilkan blok
   `[PERHATIAN] Masih TUTUP: ...` bila ada yang belum dibuka). Jadwal terisi tampil di menu
   Lihat Studio tanpa nama penyewa (hanya kini & depan — yang tanggalnya
   sudah lewat otomatis hilang dari layar, realtime saat booking);
   menu operator 7 menampilkan booking hari ini per studio untuk
   menilai full/tidak.
7. **Pembayaran**: jumlah otomatis = `total_biaya` (sewa `Pending`)
   atau `denda` (`Selesai` berdenda); hanya milik sendiri; duplikat
   `Menunggu` ditolak; metode hanya `Tunai | Transfer`.
   **Tunai** = cash di lokasi, **tanpa foto** (`bukti_bayar` NULL);
   **Transfer** = wajib foto bukti. Verifikasi operator wajib cocokkan
   ID pembayaran dengan ID transaksinya, hanya `Menunggu` + transaksi
   `Pending`/`Selesai`-berdenda yang bisa diverifikasi (anti verifikasi
   ulang).
8. **Status flow**: `Pending` -> (bayar Diterima) `Lunas` -> (kembali)
   `Selesai`; bayar Ditolak -> `Batal` (pesan ulang manual di menu Sewa).
   Kembali-terlambat: `Selesai` + denda = tagihan; denda Diterima ->
   **`Tuntas`**; denda Ditolak -> tetap `Selesai` (boleh bayar ulang).
   Pengembalian butuh status `Lunas`.
9. **Denda**: Rp20.000/hari keterlambatan
   (`tgl_kembali_aktual - tgl_kembali_rencana`, tepat waktu = 0).
10. **Laporan owner**: pendapatan = `SUM(total_biaya)` untuk status
    `Lunas + Selesai + Tuntas` + `SUM(denda)` hanya yang sudah dibayar
    (`Tuntas`); `Pending`/`Batal` dikecualikan (ditampilkan
    sebagai info). Bulanan dikelompokkan per `tgl_sewa` (`YYYY-MM`).
11. Semua input salah (ID, tanggal, status) mengembalikan pesan ramah,
    tidak pernah crash (`ValueError`/`TypeError` ditangani di controller).

---

## 4. Menu per Role

- **Penyewa**: 1 lihat alat, 2 lihat studio (+ jadwal terisi per jam),
  3 sewa studio (pilih bernomor → tanggal → jam mulai + durasi),
  4 sewa alat (tanggal → pilih bernomor + keranjang → tanggal kembali),
  5 bayar bernomor (sewa Pending + denda Selesai; Tunai tanpa foto /
  Transfer wajib bukti), 6 pesanan & riwayat milik sendiri (status
  transaksi + bayar + denda + rincian item).
- **Operator**: 1 tambah alat, 2 tambah studio (stok >= 0, kapasitas > 0,
  tarif gaya Indonesia `50.000`/`50.000,50`, salah ketik tidak crash),
  3 verifikasi bayar (tampil metode/bukti, pilih antrean bernomor,
  ID-Bayar otomatis, 1.Diterima/2.Ditolak, tolak verifikasi ulang +
  cek slot direbut), 4 pengembalian (daftar aktif + estimasi TERLAMBAT,
  rincian item, denda masuk tagihan), 5 pesanan pending,
  6 riwayat (Selesai/Lunas/Batal/Tuntas), 7 atur status studio
  (info booking hari ini, `Buka`/`Tandai Full Hari Ini`/Maintenance +
  konfirmasi full), 8 edit/hapus data studio (batal di mana saja,
  hapus kunci `HAPUS`, tolak bila pernah dipakai).
- **Owner**: 1-3 hanya lihat (rekap, riwayat + filter status, bulanan
  + filter `YYYY-MM`), tanpa menyimpan file. 4 cetak ke TXT (pilih salah
  satu atau semuanya sekaligus).

---

## 5. Kondisi Awal DB Fresh (acuan UAT §7)

- `users` 6: Owner `Setiawan`, Operator `bimo`,
  Penyewa `suci/kila/fatih/nanda` (no HP unik).
- `studio` 4 (id 2-5: A Painting, B Keramik, C Digital, D Mini),
  **semua `Tersedia`**, tarif per jam sesuai DB.
- `alat` 9 (id 3-11) dengan stok awal (Easel 10, Projector 3, dst).
- `transaksi`, `detail_transaksi`, `pembayaran`: **0 baris**,
  `AUTO_INCREMENT` transaksi = 1.
- Backup: DB `artstudio_rent_bak` + file dump di temp opencode.
- Contoh telat/denda/`Tuntas` TIDAK tersedia di awal — dibuat saat
  UAT langkah 10-11, lalu DB di-reset fresh lagi (§7 langkah 16).

---

## 6. Checklist Verifikasi (untuk AI pemeriksa)

1. `SHOW TABLES` tepat 6 tabel di atas (tidak ada tabel tambahan).
2. Semua query memakai nama kolom seksi 2 (tidak ada `id_pengguna`,
   `tanggal_pesan`, `kategori`, `tarif_sewa`, tabel `pengembalian`).
3. ENUM `status_transaksi` = `Pending,Lunas,Selesai,Batal,Tuntas`
   (default `Pending`).
4. Alur penuh sukses: pesan -> bayar -> verifikasi Diterima ->
   kembali (stok pulih, status `Selesai`) -> bayar denda ->
   verifikasi -> `Tuntas`.
5. Penolakan: stok kurang/negatif, kapasitas 0, tanggal masa lalu,
   jam tutup 22.00, tanggal-jam overlap (`Lunas`), studio
   maintenance/Dibooking, bayar ganda/milik orang lain/salah status,
   verifikasi ulang, verifikasi ID silang, slot direbut, kembali
   sebelum sewa, registrasi kosong, input tanggal/ID/angka salah.
6. Rekap owner = `SUM(total_biaya)` atas `Lunas+Selesai+Tuntas` +
   `SUM(denda)` atas `Tuntas` saja; cocok hitung manual.
7. `python -m py_compile` lolos untuk semua file `models/ controllers/
   views/` + `main.py`.

---

## 7. Skenario UAT Manual (jalan di DB fresh §5)

Jalankan dengan `.\env\Scripts\python.exe main.py`. Tanggal pakai
relatif: `BESOK` = besok, `LUSA` = lusa. Studio B = Rp75.000/jam.

### A. Auth (Penyewa: `kila`)
1. Registrasi: kosongkan semua -> ditolak *"wajib diisi"*; email
   tanpa `@` -> ditolak; daftar `uat1` valid -> sukses, lalu login.
2. Login salah password -> *"Username/Email atau Password salah!"*.

### B. Pesan & bayar (`kila`)
3. Sewa Studio B: `BESOK`, jam 10, 2 jam -> sukses, catat KODE-A.
   Total harapan: Rp150.000.
4. Sewa Studio B: tanggal kemarin -> ditolak *"masa lalu"*;
   jam 21 durasi 2 -> ditolak *"Tutup jam 22.00"*.
5. Sewa Alat: Easel x2, sewa `BESOK` kembali 2 hari sesudahnya
   (opsi 2. Lusa) -> sukses. Harapan: Rp25.000 x 2 x 2 hari
   = Rp100.000; stok Easel 10 -> 8.
6. Bayar KODE-A Tunai (tanpa foto) -> sukses; bayar alat Transfer
   tanpa file -> ditolak; dengan file `tf.jpg` -> sukses.
7. Menu 6: KODE-A `Pending/Tunai`, alat `Pending/Transfer`,
   rincian jam 10.00-12.00 tampil.

### C. Rebutan slot (`fatih` + Operator `bimo`)
8. `fatih` pesan Studio B slot SAMA (`BESOK` jam 10, 2 jam) ->
   sukses (Pending tak mengunci). Bayar Tunai.
9. Operator menu 3: verifikasi KODE-A Diterima -> `Lunas`;
   verifikasi pesanan alat Diterima -> `Lunas`; verifikasi pesanan
   `fatih` Diterima -> ditolak *"direbut"*; verifikasi ulang KODE-A
   -> ditolak *"tidak bisa diverifikasi ulang"*; lalu `Ditolak` ->
   `Batal` + arahan pesan baru.

### D. Kembali + denda (`bimo`, `kila`)
10. Operator menu 4: KODE-A `TERLAMBAT` (kembalikan aktual `LUSA` =
    telat 1 hari) -> denda Rp20.000 + pesan *"masuk tagihan"*;
    stok Easel TIDAK berubah (pesanan studio).
11. `kila` menu 5: ada baris `DENDA Rp20.000` -> bayar Tunai.
    Operator verifikasi -> `Tuntas`. Menu 6: status `Tuntas`.
12. Kembalikan pesanan alat tepat waktu -> `Selesai`, stok Easel
    8 -> 10.

### E. Inventaris (`bimo`)
13. Menu 1: stok `-5` ditolak; tarif `50.000,50` diterima.
    Menu 2: kapasitas `0` ditolak. Menu 7: tandai full butuh
    konfirmasi `1`; batal -> tanpa perubahan. Menu 8: semua Enter
    -> batal otomatis; hapus Studio B -> ditolak (pernah dipakai).

### F. Owner (`Setiawan`)
14. Rekap: sewa Rp150.000 + Rp100.000 = Rp250.000;
    denda `Tuntas` Rp20.000; total Rp270.000 (hitung manual cocok;
    angka ini berlaku bila mulai dari §5 — bila ada transaksi lain,
    cocokkan rekap dengan `SUM` manual). Filter riwayat `Tuntas`
    tampil 1 baris; cetak TXT sukses (hapus file TXT setelah cek).

### G. Robustness
15. `Ctrl+C` di menu mana pun -> keluar rapi tanpa traceback.

### H. Reset fresh
16. `TRUNCATE detail_transaksi, pembayaran, transaksi`
    (`SET FOREIGN_KEY_CHECKS=0/1`); pastikan 0 semua +
    `AUTO_INCREMENT` transaksi = 1. Selesai: DB kembali §5.
