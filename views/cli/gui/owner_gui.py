
import sys
import os
import customtkinter as ctk
from tkinter import ttk, messagebox
import mysql.connector

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class OwnerGUI(ctk.CTk):
    def __init__(self, user):
        super().__init__()

        self.user = user or {}
        nama_user = (
            self.user.get("nama_lengkap")
            or self.user.get("username")
            or "Owner"
        )

        self.title(
            f"ArtStudio-Rent — Dashboard Owner / Pemilik Studio "
            f"({str(nama_user).title()})"
        )
        self.geometry("1100x650")
        self.overrideredirect(False)
        self.resizable(True, True)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ================= HEADER =================
        header_frame = ctk.CTkFrame(
            self, fg_color="transparent"
        )
        header_frame.grid(
            row=0, column=0, sticky="ew",
            padx=15, pady=(15, 0)
        )

        ctk.CTkLabel(
            header_frame,
            text=f"Owner Dashboard — {str(nama_user).title()}",
            font=("Segoe UI", 16, "bold"),
            text_color="#ffffff"
        ).pack(side="left")

        ctk.CTkButton(
            header_frame,
            text="Keluar (Logout)",
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=("Segoe UI", 11, "bold"),
            width=120,
            height=32,
            command=self.aksi_logout
        ).pack(side="right")

        # ================= STYLING TABEL =================
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="#ffffff",
            fieldbackground="#2b2b2b",
            rowheight=28,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Treeview.Heading",
            background="#1f538d",
            foreground="#ffffff",
            font=("Segoe UI", 10, "bold")
        )

        style.map(
            "Treeview",
            background=[("selected", "#1f456e")]
        )

        # ================= TAB UTAMA =================
        self.tab_view = ctk.CTkTabview(
            self,
            fg_color="#1a1a1a",
            segmented_button_fg_color="#2b2b2b"
        )
        self.tab_view.grid(
            row=1, column=0, sticky="nsew",
            padx=15, pady=10
        )

        self.tab_laporan = self.tab_view.add(
            "Rekapitulasi & Laporan Pendapatan"
        )
        self.tab_analisis = self.tab_view.add(
            "Analisis Utilisasi Alat & Studio"
        )

        self.setup_tab_laporan()
        self.setup_tab_analisis()

    # ==================================================
    # TAB LAPORAN PENDAPATAN
    # ==================================================
    def setup_tab_laporan(self):
        self.tab_laporan.grid_columnconfigure(0, weight=1)
        self.tab_laporan.grid_rowconfigure(1, weight=1)

        top_f = ctk.CTkFrame(
            self.tab_laporan,
            fg_color="#222222",
            corner_radius=10
        )
        top_f.grid(
            row=0, column=0, sticky="ew",
            padx=10, pady=(10, 5)
        )

        ctk.CTkLabel(
            top_f,
            text="Laporan Pendapatan",
            font=("Segoe UI", 15, "bold")
        ).pack(side="left", padx=20, pady=15)

        self.lbl_total = ctk.CTkLabel(
            top_f,
            text="Total Pendapatan (Lunas): Rp 0",
            font=("Segoe UI", 15, "bold"),
            text_color="#2ecc71"
        )
        self.lbl_total.pack(
            side="right", padx=20, pady=15
        )

        table_frame = ctk.CTkFrame(
            self.tab_laporan,
            fg_color="transparent"
        )
        table_frame.grid(
            row=1, column=0, sticky="nsew",
            padx=10, pady=5
        )

        kolom = (
            "id_trx",
            "tanggal",
            "id_user",
            "penyewa",
            "total",
            "status"
        )

        self.tabel_laporan = ttk.Treeview(
            table_frame,
            columns=kolom,
            show="headings",
            height=13
        )

        self.tabel_laporan.heading(
            "id_trx", text="ID Transaksi"
        )
        self.tabel_laporan.heading(
            "tanggal", text="Tanggal Sewa"
        )
        self.tabel_laporan.heading(
            "id_user", text="ID Penyewa"
        )
        self.tabel_laporan.heading(
            "penyewa", text="Nama Penyewa"
        )
        self.tabel_laporan.heading(
            "total", text="Total Biaya"
        )
        self.tabel_laporan.heading(
            "status", text="Status Transaksi"
        )

        self.tabel_laporan.column(
            "id_trx", width=90, anchor="center"
        )
        self.tabel_laporan.column(
            "tanggal", width=130, anchor="center"
        )
        self.tabel_laporan.column(
            "id_user", width=90, anchor="center"
        )
        self.tabel_laporan.column(
            "penyewa", width=170, anchor="w"
        )
        self.tabel_laporan.column(
            "total", width=140, anchor="center"
        )
        self.tabel_laporan.column(
            "status", width=120, anchor="center"
        )

        scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tabel_laporan.yview
        )
        self.tabel_laporan.configure(
            yscrollcommand=scroll.set
        )

        self.tabel_laporan.pack(
            side="left", fill="both", expand=True
        )
        scroll.pack(side="right", fill="y")

        btn_f = ctk.CTkFrame(
            self.tab_laporan,
            fg_color="transparent"
        )
        btn_f.grid(
            row=2, column=0, sticky="ew",
            padx=10, pady=10
        )

        ctk.CTkButton(
            btn_f,
            text="Cetak / Export Laporan Bulanan",
            fg_color="#2980b9",
            height=42,
            command=self.aksi_export
        ).pack(
            side="left", expand=True, fill="x",
            padx=(0, 10)
        )

        ctk.CTkButton(
            btn_f,
            text="Segarkan Data Laporan",
            fg_color="#3498db",
            height=42,
            command=self.muat_data_owner
        ).pack(
            side="right", expand=True, fill="x",
            padx=(10, 0)
        )

        self.muat_data_owner()

    # ==================================================
    # TAB ANALISIS
    # ==================================================
    def setup_tab_analisis(self):
        self.tab_analisis.grid_columnconfigure(
            0, weight=1
        )
        self.tab_analisis.grid_rowconfigure(
            1, weight=1
        )

        ctk.CTkLabel(
            self.tab_analisis,
            text="Statistik & Analisis Utilisasi Alat & Studio",
            font=("Segoe UI", 15, "bold")
        ).grid(
            row=0, column=0, sticky="w",
            padx=15, pady=(15, 5)
        )

        table_frame = ctk.CTkFrame(
            self.tab_analisis,
            fg_color="transparent"
        )
        table_frame.grid(
            row=1, column=0, sticky="nsew",
            padx=10, pady=5
        )

        kolom = (
            "nama_ruangan",
            "kategori",
            "total_disewa",
            "pendapatan_alat"
        )

        self.tabel_analisis = ttk.Treeview(
            table_frame,
            columns=kolom,
            show="headings",
            height=13
        )

        self.tabel_analisis.heading(
            "nama_ruangan", text="Nama Alat / Studio"
        )
        self.tabel_analisis.heading(
            "kategori", text="Kategori"
        )
        self.tabel_analisis.heading(
            "total_disewa", text="Frekuensi Disewa"
        )
        self.tabel_analisis.heading(
            "pendapatan_alat",
            text="Kontribusi Pendapatan"
        )

        self.tabel_analisis.column(
            "nama_ruangan", width=220, anchor="w"
        )
        self.tabel_analisis.column(
            "kategori", width=150, anchor="w"
        )
        self.tabel_analisis.column(
            "total_disewa", width=140, anchor="center"
        )
        self.tabel_analisis.column(
            "pendapatan_alat", width=180, anchor="center"
        )

        scroll = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tabel_analisis.yview
        )
        self.tabel_analisis.configure(
            yscrollcommand=scroll.set
        )

        self.tabel_analisis.pack(
            side="left", fill="both", expand=True
        )
        scroll.pack(side="right", fill="y")

        self.muat_data_analisis()

    # ==================================================
    # MEMUAT LAPORAN DARI DATABASE
    # ==================================================
    def muat_data_owner(self):
        for r in self.tabel_laporan.get_children():
            self.tabel_laporan.delete(r)

        total_lunas = 0
        db = None
        cursor = None

        try:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="artstudio_rent"
            )

            cursor = db.cursor(dictionary=True)

            query = """
                SELECT
                    t.id_transaksi,
                    t.tgl_sewa,
                    t.id_user,
                    t.total_biaya,
                    t.status_transaksi,
                    u.nama_lengkap,
                    u.username
                FROM transaksi AS t
                LEFT JOIN users AS u
                    ON t.id_user = u.id_user
                ORDER BY t.id_transaksi DESC
            """

            cursor.execute(query)
            transaksi_list = cursor.fetchall()

            for t in transaksi_list:
                biaya = float(t.get("total_biaya") or 0)
                status = str(
                    t.get("status_transaksi") or "Pending"
                )

                nama_penyewa = (
                    t.get("nama_lengkap")
                    or t.get("username")
                    or f"User {t.get('id_user')}"
                )

                if status.lower() in (
                    "lunas", "selesai", "paid"
                ):
                    total_lunas += biaya

                self.tabel_laporan.insert(
                    "",
                    "end",
                    values=(
                        t.get("id_transaksi"),
                        t.get("tgl_sewa") or "-",
                        t.get("id_user"),
                        nama_penyewa,
                        f"Rp {biaya:,.0f}",
                        status
                    )
                )

            self.lbl_total.configure(
                text=(
                    "Total Pendapatan (Lunas): "
                    f"Rp {total_lunas:,.0f}"
                )
            )

        except mysql.connector.Error as err:
            messagebox.showerror(
                "Database Error",
                f"Gagal memuat laporan:\n{err}"
            )

        finally:
            if cursor is not None:
                cursor.close()

            if db is not None and db.is_connected():
                db.close()

    # ==================================================
    # ANALISIS UTILISASI
    # ==================================================
    def muat_data_analisis(self):
        for r in self.tabel_analisis.get_children():
            self.tabel_analisis.delete(r)

        # Struktur tabel transaksi yang tersedia belum
        # memiliki kolom nama_alat atau ID alat.
        # Karena itu, analisis alat belum dapat dihitung
        # secara akurat dari database saat ini.
        self.tabel_analisis.insert(
            "",
            "end",
            values=(
                "Belum tersedia",
                "-",
                "-",
                "Perlu relasi tabel alat"
            )
        )

    # ==================================================
    # EXPORT LAPORAN
    # ==================================================
    def aksi_export(self):
        messagebox.showinfo(
            "Informasi",
            "Fitur export belum diimplementasikan. "
            "Data laporan sudah dapat dilihat di dashboard."
        )

    # ==================================================
    # LOGOUT
    # ==================================================
    def aksi_logout(self):
        if messagebox.askyesno(
            "Konfirmasi",
            "Apakah Anda ingin keluar ke halaman login?"
        ):
            self.destroy()
            from login_gui import LoginGUI
            LoginGUI().mainloop()


# ======================================================
# MENJALANKAN DASHBOARD
# ======================================================
if __name__ == "__main__":
    if len(sys.argv) >= 4:
        user = {
            "id_user": int(sys.argv[1]),
            "nama_lengkap": sys.argv[2],
            "role": sys.argv[3]
        }
        OwnerGUI(user).mainloop()
    else:
        print(
            "Silakan jalankan dashboard melalui login_gui.py."
        )
