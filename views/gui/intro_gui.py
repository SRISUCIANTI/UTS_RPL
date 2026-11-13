"""Layar intro (splash) ArtStudio-Rent.

Dipanggil dari main.py sebelum halaman login muncul. Memakai logo dan palet
warna yang sama dengan login_gui.py, jadi tampilannya menyatu.

Urutan animasi (total sekitar 3,4 detik):
  1. jendela muncul perlahan (fade in)
  2. logo naik dari bawah dengan gerak melambat
  3. nama aplikasi dan tagline muncul bergantian
  4. bar progres terisi sambil berganti teks status
  5. jendela memudar, lalu halaman login tampil

Klik atau tekan Esc kapan saja untuk melewati intro.
"""

import time
import tkinter

import customtkinter as ctk

from views.gui.login_gui import (
    LOGO_PATH,
    LOGO_PATH_GELAP,
    WARNA_GARIS,
    WARNA_KARTU,
    WARNA_LATAR,
    WARNA_TEKS,
    WARNA_TEKS_REDUP,
    WARNA_UTAMA,
    _potong_tepi,
)

# ---------------------------------------------------------------
# PENGATURAN (ubah di sini bila ingin intro lebih cepat/lambat)
# ---------------------------------------------------------------
LEBAR, TINGGI = 460, 520
UKURAN_LOGO = 170
NAMA_APP = "ArtStudio-Rent"
TAGLINE = "Sewa studio & alat lukis, jadi lebih mudah"

T_FADE_IN = (0.00, 0.45)     # jendela muncul
T_LOGO = (0.15, 1.05)        # logo naik
T_JUDUL = (0.85, 1.45)       # nama aplikasi
T_TAGLINE = (1.30, 1.90)     # tagline
T_PROGRES = (1.00, 3.00)     # bar progres terisi
T_FADE_OUT = (3.10, 3.50)    # jendela memudar
T_TOTAL = T_FADE_OUT[1]

STATUS = [  # (mulai progres 0-1, teks)
    (0.00, "Menyiapkan kanvas..."),
    (0.40, "Merapikan alat lukis..."),
    (0.80, "Siap digunakan!"),
]

Y_LOGO, Y_JUDUL, Y_TAGLINE, Y_BAR, Y_STATUS = 170, 322, 364, 430, 458
JARAK_NAIK_LOGO = 45         # logo mulai sekian piksel di bawah posisi akhir
JARAK_NAIK_JUDUL = 14


# ---------------------------------------------------------------
# FUNGSI BANTU
# ---------------------------------------------------------------
def _ease_out(t):
    return 1 - (1 - t) ** 3


def _ease_in_out(t):
    return 3 * t * t - 2 * t * t * t


def _porsi(t, rentang):
    """Ubah waktu t menjadi 0..1 di dalam rentang (mulai, selesai)."""
    mulai, selesai = rentang
    if t <= mulai:
        return 0.0
    if t >= selesai:
        return 1.0
    return (t - mulai) / (selesai - mulai)


def _hex_ke_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _campur(c1, c2, t):
    """Campur dua warna hex dengan porsi t (0 = c1, 1 = c2)."""
    a, b = _hex_ke_rgb(c1), _hex_ke_rgb(c2)
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def _campur_tema(pasangan_awal, pasangan_akhir, t):
    """Sama seperti _campur, tetapi untuk pasangan warna (terang, gelap)."""
    return (
        _campur(pasangan_awal[0], pasangan_akhir[0], t),
        _campur(pasangan_awal[1], pasangan_akhir[1], t),
    )


# ---------------------------------------------------------------
# JENDELA INTRO
# ---------------------------------------------------------------
class IntroGUI(ctk.CTkToplevel):
    """Splash screen. Membuat dirinya sendiri di atas jendela induk (login)
    yang disembunyikan, lalu menampilkan induk kembali saat selesai."""

    def __init__(self, induk):
        super().__init__(induk)
        self.induk = induk
        self._selesai = False
        self._after_id = None

        induk.withdraw()  # sembunyikan login selama intro

        self.title("ArtStudio-Rent")
        self.configure(fg_color=WARNA_LATAR)
        self.overrideredirect(True)  # tanpa bingkai/tombol jendela
        self._atur_alpha(0.0)
        self._tengahkan()
        try:
            self.attributes("-topmost", True)
        except tkinter.TclError:
            pass

        self._bangun_tampilan()

        self.bind("<Button-1>", self._lewati)
        self.bind("<Escape>", self._lewati)
        self.protocol("WM_DELETE_WINDOW", self._akhiri)

        self.update_idletasks()
        self._t0 = time.perf_counter()
        self._tick()

    # ----- persiapan jendela -----
    def _atur_alpha(self, nilai):
        try:
            self.attributes("-alpha", max(0.0, min(1.0, nilai)))
        except tkinter.TclError:
            pass  # sistem tanpa dukungan transparansi: abaikan fade

    def _tengahkan(self):
        """Taruh jendela di tengah layar (memakai piksel asli agar benar di layar HiDPI)."""
        try:
            skala = self._get_window_scaling()
        except Exception:
            skala = 1.0
        lebar, tinggi = int(LEBAR * skala), int(TINGGI * skala)
        x = (self.winfo_screenwidth() - lebar) // 2
        y = (self.winfo_screenheight() - tinggi) // 2
        tkinter.Wm.wm_geometry(self, f"{lebar}x{tinggi}+{x}+{max(0, y - 20)}")

    def _bangun_tampilan(self):
        self.kartu = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color=WARNA_KARTU,
            border_width=2,
            border_color=WARNA_GARIS,
        )
        self.kartu.pack(fill="both", expand=True, padx=8, pady=8)

        self.logo_image = self._muat_logo()
        self.lbl_logo = ctk.CTkLabel(self.kartu, image=self.logo_image, text="") if self.logo_image else None

        self.lbl_judul = ctk.CTkLabel(
            self.kartu, text=NAMA_APP, font=("Segoe UI", 30, "bold"), text_color=WARNA_KARTU
        )
        self.lbl_tagline = ctk.CTkLabel(
            self.kartu, text=TAGLINE, font=("Segoe UI", 13), text_color=WARNA_KARTU
        )
        self.bar = ctk.CTkProgressBar(
            self.kartu,
            width=250,
            height=6,
            corner_radius=3,
            fg_color=WARNA_GARIS,
            progress_color=WARNA_UTAMA,
        )
        self.bar.set(0)
        self.lbl_status = ctk.CTkLabel(
            self.kartu, text=STATUS[0][1], font=("Segoe UI", 11), text_color=WARNA_KARTU
        )

        # posisi awal (animasi akan menggesernya)
        self._taruh(self.lbl_logo, Y_LOGO + JARAK_NAIK_LOGO)
        self._taruh(self.lbl_judul, Y_JUDUL + JARAK_NAIK_JUDUL)
        self._taruh(self.lbl_tagline, Y_TAGLINE)
        self._taruh(self.bar, Y_BAR)
        self._taruh(self.lbl_status, Y_STATUS)

    def _muat_logo(self):
        """Logo terang dan gelap, dipotong rapi seperti di halaman login. None bila gagal."""
        try:
            from PIL import Image

            terang = _potong_tepi(Image.open(LOGO_PATH))
            gelap = terang
            try:
                gelap = _potong_tepi(Image.open(LOGO_PATH_GELAP))
                if gelap.size != terang.size:
                    gelap = gelap.resize(terang.size, Image.LANCZOS)
            except Exception:
                gelap = terang
            lebar, tinggi = terang.size
            skala = UKURAN_LOGO / max(lebar, tinggi)
            ukuran = (max(1, int(lebar * skala)), max(1, int(tinggi * skala)))
            return ctk.CTkImage(light_image=terang, dark_image=gelap, size=ukuran)
        except Exception:
            return None

    @staticmethod
    def _taruh(widget, y):
        if widget is not None:
            widget.place(relx=0.5, y=y, anchor="center")

    # ----- animasi -----
    def _tick(self):
        if self._selesai or not self.winfo_exists():
            return
        t = time.perf_counter() - self._t0

        # 1. jendela muncul dan menghilang
        alpha = _porsi(t, T_FADE_IN) * (1 - _porsi(t, T_FADE_OUT))
        self._atur_alpha(alpha)

        # 2. logo naik
        naik = _ease_out(_porsi(t, T_LOGO))
        self._taruh(self.lbl_logo, Y_LOGO + JARAK_NAIK_LOGO * (1 - naik))

        # 3. judul dan tagline (warna memudar dari latar kartu ke warna teks)
        p_judul = _ease_out(_porsi(t, T_JUDUL))
        self.lbl_judul.configure(text_color=_campur_tema(WARNA_KARTU, WARNA_TEKS, p_judul))
        self._taruh(self.lbl_judul, Y_JUDUL + JARAK_NAIK_JUDUL * (1 - p_judul))

        p_tag = _ease_out(_porsi(t, T_TAGLINE))
        self.lbl_tagline.configure(text_color=_campur_tema(WARNA_KARTU, WARNA_TEKS_REDUP, p_tag))

        # 4. progres + status
        p_bar = _ease_in_out(_porsi(t, T_PROGRES))
        self.bar.set(p_bar)
        status = STATUS[0][1]
        for batas, teks in STATUS:
            if p_bar >= batas:
                status = teks
        self.lbl_status.configure(
            text=status,
            text_color=_campur_tema(WARNA_KARTU, WARNA_TEKS_REDUP, _porsi(t, (T_PROGRES[0], T_PROGRES[0] + 0.3))),
        )

        if t >= T_TOTAL:
            self._akhiri()
            return
        self._after_id = self.after(15, self._tick)

    def _lewati(self, _event=None):
        """Loncat ke tahap memudar supaya intro bisa dilewati."""
        t = time.perf_counter() - self._t0
        if t < T_FADE_OUT[0]:
            self._t0 -= T_FADE_OUT[0] - t

    def _akhiri(self):
        if self._selesai:
            return
        self._selesai = True
        if self._after_id is not None:
            try:
                self.after_cancel(self._after_id)
            except Exception:
                pass
        try:
            self.destroy()
        except Exception:
            pass
        try:
            self.induk.deiconify()
            self.induk.lift()
            self.induk.focus_force()
        except Exception:
            pass