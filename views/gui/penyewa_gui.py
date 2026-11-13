import os
import sys
import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
from datetime import date, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


# ---------------------------------------------------------------
# FUNGSI BANTU TAMPILAN KATALOG (murni, tanpa GUI/DB agar mudah diuji)
# ---------------------------------------------------------------
def format_rupiah(nilai):
    """Rp 25.000 (tanpa desimal bila bulat) / Rp 25.000,50."""
    nilai = float(nilai or 0)
    if nilai == int(nilai):
        teks = f"{int(nilai):,}".replace(",", ".")
    else:
        teks = f"{nilai:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"Rp {teks}"


def format_jam(nilai):
    """Kolom TIME MySQL (timedelta / time / 'HH:MM:SS') -> '10.00'. None -> None.
    Aman untuk 24.00 (timedelta 1 hari)."""
    if nilai is None:
        return None
    if isinstance(nilai, timedelta):
        jam, sisa = divmod(int(nilai.total_seconds()), 3600)
        menit = sisa // 60
    elif hasattr(nilai, "hour"):
        jam, menit = nilai.hour, nilai.minute
    else:
        bagian = str(nilai).split(":")
        jam, menit = int(bagian[0]), int(bagian[1])
    return f"{jam:02d}.{menit:02d}"


def format_tanggal(nilai):
    return nilai.strftime("%d-%m-%Y") if hasattr(nilai, "strftime") else str(nilai)


def format_slot_jadwal(tgl_sewa, tgl_kembali, jam_mulai, jam_selesai):
    """Satu baris jadwal terisi -> (teks tanggal, teks jam).
    Baris tanpa jam dianggap memenuhi seharian (aturan Plan.md poin 6)."""
    tgl = format_tanggal(tgl_sewa)
    if tgl_kembali and tgl_kembali != tgl_sewa:
        tgl += f" s/d {format_tanggal(tgl_kembali)}"
    mulai, selesai = format_jam(jam_mulai), format_jam(jam_selesai)
    jam = f"{mulai} - {selesai}" if mulai and selesai else "Seharian"
    return tgl, jam


class PenyewaGUI(ctk.CTk):
    def __init__(self, user):
        super().__init__()

        self.user = user or {}
        self.id_user = self.user.get("id_user") or self.user.get("id")
        nama_user = (
            self.user.get("nama_lengkap")
            or self.user.get("username")
            or "Penyewa"
        )

        self.title(
            f"ArtStudio-Rent — Dashboard Penyewa ({str(nama_user).title()})"
        )
        self.geometry("1150x680")
        self.resizable(True, True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(
            row=0, column=0, sticky="ew", padx=15, pady=(15, 0)
        )

        ctk.CTkLabel(
            header_frame,
            text=f"Halo, {str(nama_user).title()} (Penyewa)",
            font=("Segoe UI", 16, "bold"),
            text_color="#ffffff",
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="Keluar (Logout)",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            width=120,
            height=32,
            command=self.aksi_logout,
        ).pack(side="right")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="#ffffff",
            fieldbackground="#2b2b2b",
            rowheight=28,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background="#1f538d",
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Treeview", background=[("selected", "#1f456e")])

        self.tab_view = ctk.CTkTabview(
            self,
            fg_color="#1a1a1a",
            segmented_button_fg_color="#2b2b2b",
        )
        self.tab_view.grid(
            row=1, column=0, sticky="nsew", padx=15, pady=10
        )

        self.tab_katalog = self.tab_view.add("Daftar Studio & Alat")
        self.tab_pesan = self.tab_view.add("Buat Pesanan Studio")
        self.tab_bayar = self.tab_view.add("Bayar Pesanan & Denda")
        self.tab_riwayat = self.tab_view.add("Pesanan & Riwayat Saya")

        self.setup_tab_katalog()
        self.setup_tab_pesan()
        self.setup_tab_bayar()
        self.setup_tab_riwayat()

    def setup_tab_katalog(self):
        self._studio_status = {}  # id_studio -> status_ketersediaan

        self.tab_katalog.grid_columnconfigure(0, weight=1)
        self.tab_katalog.grid_rowconfigure(1, weight=3)
        self.tab_katalog.grid_rowconfigure(3, weight=2)

        ctk.CTkLabel(
            self.tab_katalog,
            text="Katalog Studio Seni",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 4))

        # ---- baris atas: tabel studio (kiri) + jadwal terisi (kanan) ----
        atas = ctk.CTkFrame(self.tab_katalog, fg_color="transparent")
        atas.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
        atas.grid_columnconfigure(0, weight=5)
        atas.grid_columnconfigure(1, weight=3)
        atas.grid_rowconfigure(0, weight=1)

        f_studio = ctk.CTkFrame(atas, fg_color="transparent")
        f_studio.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        kolom = ("id_studio", "nama", "harga", "kapasitas", "fasilitas", "status")
        self.tabel_katalog = ttk.Treeview(
            f_studio, columns=kolom, show="headings", height=6
        )
        self.tabel_katalog.heading("id_studio", text="ID")
        self.tabel_katalog.heading("nama", text="Nama Studio")
        self.tabel_katalog.heading("harga", text="Harga / Jam")
        self.tabel_katalog.heading("kapasitas", text="Kapasitas")
        self.tabel_katalog.heading("fasilitas", text="Fasilitas")
        self.tabel_katalog.heading("status", text="Status")

        self.tabel_katalog.column("id_studio", width=40, anchor="center")
        self.tabel_katalog.column("nama", width=150, anchor="w")
        self.tabel_katalog.column("harga", width=90, anchor="center")
        self.tabel_katalog.column("kapasitas", width=65, anchor="center")
        self.tabel_katalog.column("fasilitas", width=200, anchor="w")
        self.tabel_katalog.column("status", width=85, anchor="center")
        self.tabel_katalog.bind("<<TreeviewSelect>>", self.pilih_studio_katalog)

        scroll = ttk.Scrollbar(
            f_studio, orient="vertical", command=self.tabel_katalog.yview
        )
        self.tabel_katalog.configure(yscrollcommand=scroll.set)
        self.tabel_katalog.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        f_jadwal = ctk.CTkFrame(atas, fg_color="#222222", corner_radius=10)
        f_jadwal.grid(row=0, column=1, sticky="nsew")

        self.lbl_judul_jadwal = ctk.CTkLabel(
            f_jadwal,
            text="Jadwal Terisi",
            font=("Segoe UI", 13, "bold"),
        )
        self.lbl_judul_jadwal.pack(anchor="w", padx=12, pady=(10, 4))

        f_tabel_jadwal = ctk.CTkFrame(f_jadwal, fg_color="transparent")
        f_tabel_jadwal.pack(fill="both", expand=True, padx=10)

        self.tabel_jadwal = ttk.Treeview(
            f_tabel_jadwal, columns=("tanggal", "jam"), show="headings", height=4
        )
        self.tabel_jadwal.heading("tanggal", text="Tanggal")
        self.tabel_jadwal.heading("jam", text="Jam")
        self.tabel_jadwal.column("tanggal", width=150, anchor="center")
        self.tabel_jadwal.column("jam", width=110, anchor="center")
        scroll_j = ttk.Scrollbar(
            f_tabel_jadwal, orient="vertical", command=self.tabel_jadwal.yview
        )
        self.tabel_jadwal.configure(yscrollcommand=scroll_j.set)
        self.tabel_jadwal.pack(side="left", fill="both", expand=True)
        scroll_j.pack(side="right", fill="y")

        self.lbl_info_jadwal = ctk.CTkLabel(
            f_jadwal,
            text="Pilih studio pada tabel untuk melihat jadwalnya.",
            font=("Segoe UI", 11),
            text_color="#9aa0a6",
            justify="left",
            wraplength=300,
        )
        self.lbl_info_jadwal.pack(anchor="w", padx=12, pady=(6, 10))

        # ---- baris bawah: katalog alat ----
        ctk.CTkLabel(
            self.tab_katalog,
            text="Katalog Alat Lukis",
            font=("Segoe UI", 16, "bold"),
        ).grid(row=2, column=0, sticky="w", padx=10, pady=(10, 4))

        f_alat = ctk.CTkFrame(self.tab_katalog, fg_color="transparent")
        f_alat.grid(row=3, column=0, sticky="nsew", padx=10, pady=4)

        kolom_alat = ("id_alat", "nama", "harga", "stok", "deskripsi", "status")
        self.tabel_alat = ttk.Treeview(
            f_alat, columns=kolom_alat, show="headings", height=5
        )
        self.tabel_alat.heading("id_alat", text="ID")
        self.tabel_alat.heading("nama", text="Nama Alat")
        self.tabel_alat.heading("harga", text="Harga / Hari")
        self.tabel_alat.heading("stok", text="Stok")
        self.tabel_alat.heading("deskripsi", text="Deskripsi")
        self.tabel_alat.heading("status", text="Ketersediaan")

        self.tabel_alat.column("id_alat", width=40, anchor="center")
        self.tabel_alat.column("nama", width=200, anchor="w")
        self.tabel_alat.column("harga", width=110, anchor="center")
        self.tabel_alat.column("stok", width=60, anchor="center")
        self.tabel_alat.column("deskripsi", width=330, anchor="w")
        self.tabel_alat.column("status", width=100, anchor="center")
        self.tabel_alat.tag_configure("habis", foreground="#ff8a65")  # stok 0 = oranye

        scroll_a = ttk.Scrollbar(
            f_alat, orient="vertical", command=self.tabel_alat.yview
        )
        self.tabel_alat.configure(yscrollcommand=scroll_a.set)
        self.tabel_alat.pack(side="left", fill="both", expand=True)
        scroll_a.pack(side="right", fill="y")

        ctk.CTkButton(
            self.tab_katalog,
            text="Segarkan Katalog",
            fg_color="#3498db",
            command=self.muat_katalog,
        ).grid(row=4, column=0, sticky="ew", padx=10, pady=10)

        self.muat_katalog()

    def muat_katalog(self):
        """Muat ulang studio, jadwal studio terpilih, dan alat."""
        pilihan_lama = self.tabel_katalog.selection()
        for row in self.tabel_katalog.get_children():
            self.tabel_katalog.delete(row)
        self._studio_status = {}

        db = None
        cursor = None
        try:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="artstudio_rent",
            )
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM studio ORDER BY id_studio")
            for s in cursor.fetchall():
                id_studio = s.get("id_studio")
                status = s.get("status_ketersediaan") or "Tersedia"
                self._studio_status[id_studio] = status
                self.tabel_katalog.insert(
                    "",
                    "end",
                    iid=str(id_studio),
                    values=(
                        id_studio,
                        s.get("nama_studio"),
                        format_rupiah(s.get("harga_per_jam")),
                        s.get("kapasitas"),
                        s.get("fasilitas") or "-",
                        status,
                    ),
                )
        except mysql.connector.Error as err:
            messagebox.showerror(
                "Database Error", f"Gagal memuat katalog studio:\n{err}"
            )
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

        # pertahankan studio yang tadi dipilih; bila tidak ada, pilih yang pertama
        semua = self.tabel_katalog.get_children()
        if semua:
            target = pilihan_lama[0] if pilihan_lama and pilihan_lama[0] in semua else semua[0]
            self.tabel_katalog.selection_set(target)  # memicu muat_jadwal
        else:
            self.muat_jadwal(None)

        self.muat_alat()

    def pilih_studio_katalog(self, event=None):
        sel = self.tabel_katalog.selection()
        if sel:
            self.muat_jadwal(int(sel[0]))

    def muat_jadwal(self, id_studio):
        """Jadwal terisi satu studio: hanya booking Lunas masa kini dan depan,
        tanpa nama penyewa (sama dengan aturan di versi CLI)."""
        for row in self.tabel_jadwal.get_children():
            self.tabel_jadwal.delete(row)
        if id_studio is None:
            self.lbl_judul_jadwal.configure(text="Jadwal Terisi")
            self.lbl_info_jadwal.configure(text="Belum ada studio di katalog.")
            return

        nama = ""
        item = self.tabel_katalog.item(str(id_studio)).get("values")
        if item and len(item) > 1:
            nama = str(item[1])
        self.lbl_judul_jadwal.configure(text=f"Jadwal Terisi — {nama}" if nama else "Jadwal Terisi")

        status = self._studio_status.get(id_studio, "Tersedia")
        catatan = []
        if status == "Maintenance":
            catatan.append("Studio sedang dalam perawatan (Maintenance), belum bisa dipesan.")
        elif status == "Dibooking":
            catatan.append("Studio ditutup/penuh hari ini oleh operator (Dibooking).")

        db = None
        cursor = None
        try:
            db = mysql.connector.connect(
                host="localhost", user="root", password="", database="artstudio_rent"
            )
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT t.tgl_sewa, t.tgl_kembali_rencana, d.jam_mulai, d.jam_selesai
                FROM transaksi t
                JOIN detail_transaksi d ON d.id_transaksi = t.id_transaksi
                WHERE d.id_studio = %s
                  AND t.status_transaksi = 'Lunas'
                  AND t.tgl_kembali_rencana >= CURDATE()
                ORDER BY t.tgl_sewa, d.jam_mulai
                """,
                (id_studio,),
            )
            baris = cursor.fetchall()
            for b in baris:
                tgl, jam = format_slot_jadwal(
                    b.get("tgl_sewa"),
                    b.get("tgl_kembali_rencana"),
                    b.get("jam_mulai"),
                    b.get("jam_selesai"),
                )
                self.tabel_jadwal.insert("", "end", values=(tgl, jam))
            if not baris:
                catatan.append("Belum ada jadwal terisi, semua jam tersedia.")
            catatan.append("Studio tutup pukul 22.00.")
        except mysql.connector.Error as err:
            catatan.append(f"Gagal memuat jadwal: {err}")
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()
        self.lbl_info_jadwal.configure(text="\n".join(catatan))

    def muat_alat(self):
        for row in self.tabel_alat.get_children():
            self.tabel_alat.delete(row)

        db = None
        cursor = None
        try:
            db = mysql.connector.connect(
                host="localhost", user="root", password="", database="artstudio_rent"
            )
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM alat ORDER BY id_alat")
            for a in cursor.fetchall():
                stok = int(a.get("stok") or 0)
                self.tabel_alat.insert(
                    "",
                    "end",
                    values=(
                        a.get("id_alat"),
                        a.get("nama_alat"),
                        format_rupiah(a.get("harga_per_hari")),
                        stok,
                        a.get("deskripsi") or "-",
                        "Tersedia" if stok > 0 else "Habis",
                    ),
                    tags=("habis",) if stok == 0 else (),
                )
        except mysql.connector.Error as err:
            messagebox.showerror(
                "Database Error", f"Gagal memuat katalog alat:\n{err}"
            )
        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def setup_tab_pesan(self):
        ctk.CTkLabel(
            self.tab_pesan,
            text="Form Pemesanan Studio Seni",
            font=("Segoe UI", 16, "bold"),
        ).pack(pady=(20, 10))

        self.ent_alat = ctk.CTkEntry(
            self.tab_pesan,
            placeholder_text="ID Studio atau Nama Studio",
            width=350,
            height=40,
        )
        self.ent_alat.pack(pady=10)

        self.ent_durasi = ctk.CTkEntry(
            self.tab_pesan,
            placeholder_text="Durasi Sewa (Jam)",
            width=350,
            height=40,
        )
        self.ent_durasi.pack(pady=10)

        ctk.CTkButton(
            self.tab_pesan,
            text="Kirim & Buat Pesanan",
            fg_color="#3498db",
            hover_color="#2980b9",
            width=350,
            height=42,
            command=self.buat_pesanan,
        ).pack(pady=15)

    def setup_tab_bayar(self):
        self.tab_bayar.grid_columnconfigure(0, weight=1)
        self.tab_bayar.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(self.tab_bayar, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=10)

        kolom = ("id_trx", "label", "tgl", "nominal", "denda", "jenis")
        self.tabel_tagihan = ttk.Treeview(
            container, columns=kolom, show="headings", height=12
        )
        self.tabel_tagihan.heading("id_trx", text="ID Trx")
        self.tabel_tagihan.heading("label", text="Keterangan")
        self.tabel_tagihan.heading("tgl", text="Tanggal")
        self.tabel_tagihan.heading("nominal", text="Total Biaya")
        self.tabel_tagihan.heading("denda", text="Denda")
        self.tabel_tagihan.heading("jenis", text="Jenis Tagihan")

        self.tabel_tagihan.column("id_trx", width=50, anchor="center")
        self.tabel_tagihan.column("label", width=150, anchor="w")
        self.tabel_tagihan.column("tgl", width=100, anchor="center")
        self.tabel_tagihan.column("nominal", width=100, anchor="center")
        self.tabel_tagihan.column("denda", width=100, anchor="center")
        self.tabel_tagihan.column("jenis", width=100, anchor="center")

        scroll = ttk.Scrollbar(container, orient="vertical", command=self.tabel_tagihan.yview)
        self.tabel_tagihan.configure(yscrollcommand=scroll.set)
        self.tabel_tagihan.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        btn_f = ctk.CTkFrame(self.tab_bayar, fg_color="transparent")
        btn_f.pack(fill="x", pady=10)

        ctk.CTkButton(
            btn_f,
            text="Bayar via Transfer (Upload Bukti)",
            fg_color="#27ae60",
            hover_color="#219653",
            command=self.bayar_transfer,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_f,
            text="Bayar via Tunai (Cash)",
            fg_color="#f39c12",
            hover_color="#d35400",
            command=self.bayar_tunai,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_f,
            text="Segarkan Tagihan",
            fg_color="#3498db",
            command=self.muat_tagihan,
        ).pack(side="right", padx=5)

        self.muat_tagihan()

    def setup_tab_riwayat(self):
        self.tab_riwayat.grid_columnconfigure(0, weight=1)
        self.tab_riwayat.grid_rowconfigure(0, weight=1)

        container = ctk.CTkFrame(
            self.tab_riwayat, fg_color="transparent"
        )
        container.pack(fill="both", expand=True, padx=10, pady=10)

        kolom = ("id_trx", "tgl", "total", "denda", "status")
        self.tabel_riwayat = ttk.Treeview(
            container, columns=kolom, show="headings", height=13
        )

        self.tabel_riwayat.heading("id_trx", text="ID Trx")
        self.tabel_riwayat.heading("tgl", text="Tanggal Sewa")
        self.tabel_riwayat.heading("total", text="Total Biaya")
        self.tabel_riwayat.heading("denda", text="Denda")
        self.tabel_riwayat.heading("status", text="Status Pembayaran")

        self.tabel_riwayat.column("id_trx", width=60, anchor="center")
        self.tabel_riwayat.column("tgl", width=120, anchor="center")
        self.tabel_riwayat.column("total", width=120, anchor="center")
        self.tabel_riwayat.column("denda", width=110, anchor="center")
        self.tabel_riwayat.column("status", width=140, anchor="center")

        scroll = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self.tabel_riwayat.yview,
        )
        self.tabel_riwayat.configure(yscrollcommand=scroll.set)

        self.tabel_riwayat.pack(
            side="left", fill="both", expand=True
        )
        scroll.pack(side="right", fill="y")

        btn_frame = ctk.CTkFrame(self.tab_riwayat, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)

        ctk.CTkButton(
            btn_frame,
            text="Segarkan Riwayat",
            fg_color="#3498db",
            command=self.muat_riwayat,
        ).pack(side="right", padx=5)

        self.muat_riwayat()

    def buat_pesanan(self):
        input_studio = self.ent_alat.get().strip()
        durasi = self.ent_durasi.get().strip()

        if not self.id_user:
            messagebox.showerror(
                "Error Akun",
                "ID pengguna tidak ditemukan. Silakan login kembali.",
            )
            return

        if not input_studio:
            messagebox.showwarning(
                "Peringatan", "ID Studio atau Nama Studio harus diisi!"
            )
            return

        if not durasi.isdigit() or int(durasi) <= 0:
            messagebox.showwarning(
                "Peringatan",
                "Durasi sewa harus berupa angka positif (jam)!",
            )
            return

        db = None
        cursor = None

        try:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="artstudio_rent",
            )
            cursor = db.cursor(dictionary=True)

            if input_studio.isdigit():
                cursor.execute("SELECT harga_per_jam FROM studio WHERE id_studio = %s", (int(input_studio),))
            else:
                cursor.execute("SELECT harga_per_jam FROM studio WHERE nama_studio = %s", (input_studio,))
            
            hasil_studio = cursor.fetchone()

            if not hasil_studio:
                messagebox.showerror("Error", f"Studio dengan data '{input_studio}' tidak ditemukan di katalog!")
                return

            harga_per_jam = float(hasil_studio.get("harga_per_jam") or 0)
            jumlah_jam = int(durasi)
            hari_sewa = (jumlah_jam + 23) // 24
            tanggal_kembali = date.today() + timedelta(days=hari_sewa)
            total_biaya = jumlah_jam * harga_per_jam

            query_trx = """
                INSERT INTO transaksi
                (
                    id_user,
                    tgl_sewa,
                    tgl_kembali_rencana,
                    total_biaya,
                    status_transaksi
                )
                VALUES (%s, CURDATE(), %s, %s, 'Pending')
            """
            cursor.execute(
                query_trx,
                (self.id_user, tanggal_kembali, total_biaya),
            )
            id_transaksi = cursor.lastrowid

            query_byr = """
                INSERT INTO pembayaran
                (
                    id_transaksi,
                    metode_bayar,
                    jumlah_bayar,
                    status_konfirmasi
                )
                VALUES (%s, 'Transfer', %s, 'Pending')
            """
            cursor.execute(query_byr, (id_transaksi, total_biaya))
            
            db.commit()

            self.ent_alat.delete(0, "end")
            self.ent_durasi.delete(0, "end")
            self.muat_tagihan()
            self.muat_riwayat()

            messagebox.showinfo(
                "Berhasil",
                "Pesanan berhasil dibuat. Silakan buka tab 'Bayar Pesanan & Denda' untuk melakukan pembayaran.",
            )

        except mysql.connector.Error as err:
            if db and db.is_connected():
                db.rollback()
            messagebox.showerror(
                "Database Error", f"Gagal membuat pesanan:\n{err}"
            )

        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def muat_tagihan(self):
        for row in self.tabel_tagihan.get_children():
            self.tabel_tagihan.delete(row)

        if not self.id_user:
            return

        db = None
        cursor = None
        try:
            db = mysql.connector.connect(
                host="localhost", user="root", password="", database="artstudio_rent"
            )
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id_transaksi, tgl_sewa, total_biaya, denda, status_transaksi
                FROM transaksi
                WHERE id_user = %s AND status_transaksi = 'Pending'
                """,
                (self.id_user,)
            )
            for t in cursor.fetchall():
                denda_val = float(t.get('denda') or 0)
                self.tabel_tagihan.insert("", "end", values=(
                    t['id_transaksi'], "Sewa Studio", t['tgl_sewa'],
                    f"Rp {float(t['total_biaya']):,.0f}", f"Rp {denda_val:,.0f}", "Sewa Normal"
                ))
        except mysql.connector.Error as err:
            messagebox.showerror("Database Error", f"Gagal memuat tagihan:\n{err}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def bayar_transfer(self):
        sel = self.tabel_tagihan.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih tagihan pada tabel terlebih dahulu!")
            return
        item = self.tabel_tagihan.item(sel[0])
        id_trx = item.get("values")[0]

        file_path = filedialog.askopenfilename(
            title="Pilih File Bukti Pembayaran",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        db = None
        cursor = None
        try:
            db = mysql.connector.connect(
                host="localhost", user="root", password="", database="artstudio_rent"
            )
            cursor = db.cursor()
            cursor.execute("UPDATE pembayaran SET bukti_bayar = %s, metode_bayar = 'Transfer', status_konfirmasi = 'Menunggu' WHERE id_transaksi = %s", (file_path, id_trx))
            cursor.execute("UPDATE transaksi SET status_transaksi = 'Menunggu Konfirmasi' WHERE id_transaksi = %s", (id_trx,))
            db.commit()
            messagebox.showinfo("Berhasil", f"Bukti bayar untuk Transaksi ID {id_trx} berhasil diunggah!")
            self.muat_tagihan()
            self.muat_riwayat()
        except mysql.connector.Error as err:
            if db and db.is_connected(): db.rollback()
            messagebox.showerror("Database Error", f"Gagal mengunggah bukti bayar:\n{err}")
        finally:
            if cursor: cursor.close()
            if db and db.is_connected(): db.close()

    def bayar_tunai(self):
        sel = self.tabel_tagihan.selection()
        if not sel:
            messagebox.showwarning("Peringatan", "Pilih tagihan pada tabel terlebih dahulu!")
            return
        item = self.tabel_tagihan.item(sel[0])
        id_trx = item.get("values")[0]

        if messagebox.askyesno("Konfirmasi Tunai", f"Konfirmasi pembayaran tunai untuk Transaksi ID {id_trx}?"):
            db = None
            cursor = None
            try:
                db = mysql.connector.connect(
                    host="localhost", user="root", password="", database="artstudio_rent"
                )
                cursor = db.cursor()
                cursor.execute("UPDATE pembayaran SET metode_bayar = 'Tunai', status_konfirmasi = 'Menunggu' WHERE id_transaksi = %s", (id_trx,))
                cursor.execute("UPDATE transaksi SET status_transaksi = 'Menunggu Konfirmasi' WHERE id_transaksi = %s", (id_trx,))
                db.commit()
                messagebox.showinfo("Berhasil", f"Pembayaran tunai untuk Transaksi ID {id_trx} dicatat dan menunggu verifikasi operator!")
                self.muat_tagihan()
                self.muat_riwayat()
            except mysql.connector.Error as err:
                if db and db.is_connected(): db.rollback()
                messagebox.showerror("Database Error", f"Gagal mencatat pembayaran:\n{err}")
            finally:
                if cursor: cursor.close()
                if db and db.is_connected(): db.close()

    def muat_riwayat(self):
        for row in self.tabel_riwayat.get_children():
            self.tabel_riwayat.delete(row)

        if not self.id_user:
            return

        db = None
        cursor = None

        try:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="artstudio_rent",
            )
            cursor = db.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT id_transaksi, tgl_sewa,
                       total_biaya, denda, status_transaksi
                FROM transaksi
                WHERE id_user = %s
                ORDER BY id_transaksi DESC
                """,
                (self.id_user,),
            )

            for transaksi in cursor.fetchall():
                self.tabel_riwayat.insert(
                    "",
                    "end",
                    values=(
                        transaksi["id_transaksi"],
                        transaksi["tgl_sewa"],
                        f"Rp {float(transaksi['total_biaya'] or 0):,.0f}",
                        f"Rp {float(transaksi['denda'] or 0):,.0f}",
                        transaksi["status_transaksi"],
                    ),
                )

        except mysql.connector.Error as err:
            messagebox.showerror(
                "Database Error",
                f"Gagal memuat riwayat:\n{err}",
            )

        finally:
            if cursor:
                cursor.close()
            if db and db.is_connected():
                db.close()

    def aksi_logout(self):
        if messagebox.askyesno(
            "Konfirmasi",
            "Apakah Anda ingin keluar ke halaman login?",
        ):
            self.destroy()
            from login_gui import LoginGUI
            LoginGUI().mainloop()


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        user = {
            "id_user": int(sys.argv[1]),
            "nama_lengkap": sys.argv[2],
            "role": sys.argv[3],
        }
        PenyewaGUI(user).mainloop()
    else:
        user = {
            "id_user": 3,
            "nama_lengkap": "Sri Suci",
            "role": "penyewa",
        }
        PenyewaGUI(user).mainloop()