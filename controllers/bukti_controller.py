from datetime import datetime, date, timedelta
from models.transaksi_model import TransaksiModel
from models.pembayaran_model import PembayaranModel


class BuktiController:
    """FR-07: susun & simpan bukti sewa (tanda terima) satu transaksi."""

    # Bukti hanya untuk sewa yang pembayarannya sudah diterima operator.
    STATUS_BISA_CETAK = ('Lunas', 'Selesai', 'Tuntas')
    LEBAR = 60

    @staticmethod
    def _rp(nilai):
        """Rp1.250.000 (pemisah ribuan titik, gaya Indonesia)."""
        return "Rp" + f"{float(nilai or 0):,.0f}".replace(",", ".")

    @staticmethod
    def _tgl(nilai):
        if not nilai:
            return "-"
        return nilai.strftime("%Y-%m-%d") if hasattr(nilai, "strftime") else str(nilai)

    @staticmethod
    def _jam(nilai):
        """TIME MySQL (timedelta / time / 'HH:MM:SS') -> '10.00'. Aman untuk 24.00."""
        if nilai is None:
            return None
        if isinstance(nilai, timedelta):
            mnt = int(nilai.total_seconds() // 60)
            return f"{mnt // 60:02d}.{mnt % 60:02d}"
        if hasattr(nilai, "hour"):
            return f"{nilai.hour:02d}.{nilai.minute:02d}"
        bagian = str(nilai).split(":")
        return f"{int(bagian[0]):02d}.{int(bagian[1]):02d}"

    @staticmethod
    def _kiri_kanan(kiri, kanan):
        sisa = BuktiController.LEBAR - len(kiri) - len(kanan)
        return f"{kiri}{' ' * max(sisa, 1)}{kanan}"

    @staticmethod
    def susun_bukti(id_user, id_transaksi):
        """Kembalikan (True, [baris teks]) atau (False, pesan_error).

        Aturan: hanya transaksi milik sendiri; status harus Lunas/Selesai/Tuntas
        (Pending belum dibayar, Batal ditolak)."""
        try:
            id_transaksi = int(str(id_transaksi).strip())
        except (ValueError, AttributeError):
            return False, "ID Transaksi harus angka."

        trx = TransaksiModel.getById(id_transaksi)
        if not trx:
            return False, f"Transaksi ID {id_transaksi} tidak ditemukan."
        if trx['id_user'] != id_user:
            return False, "Transaksi ini bukan milik akun Anda."
        if trx['status_transaksi'] not in BuktiController.STATUS_BISA_CETAK:
            return False, (
                f"Transaksi ID {id_transaksi} statusnya '{trx['status_transaksi']}'. "
                "Bukti sewa hanya bisa dicetak setelah pembayaran diterima operator "
                "(status Lunas / Selesai / Tuntas)."
            )

        rp, tgl, kk = BuktiController._rp, BuktiController._tgl, BuktiController._kiri_kanan
        garis = "=" * BuktiController.LEBAR
        strip = "-" * BuktiController.LEBAR
        d_sewa = trx['tgl_sewa']
        d_kembali = trx['tgl_kembali_rencana']
        if isinstance(d_sewa, datetime):
            d_sewa = d_sewa.date()
        if isinstance(d_kembali, datetime):
            d_kembali = d_kembali.date()
        hari = ((d_kembali - d_sewa).days or 1) if (d_sewa and d_kembali) else 1

        baris = [
            garis,
            "ARTSTUDIO-RENT".center(BuktiController.LEBAR),
            "BUKTI SEWA / TANDA TERIMA".center(BuktiController.LEBAR),
            garis,
            f"No. Transaksi    : {trx['id_transaksi']}",
            f"Dicetak          : {datetime.now():%Y-%m-%d %H:%M}",
            f"Penyewa          : {trx['nama_lengkap']} ({trx['username']})",
            f"Status           : {trx['status_transaksi']}",
            f"Tanggal sewa     : {tgl(trx['tgl_sewa'])}",
            f"Rencana kembali  : {tgl(trx['tgl_kembali_rencana'])}",
            f"Kembali aktual   : {tgl(trx.get('tgl_kembali_aktual'))}",
            strip,
            "RINCIAN SEWA",
            strip,
        ]

        detail = TransaksiModel.lihatDetail(id_transaksi)
        for no, d in enumerate(detail, start=1):
            subtotal = rp(d.get('subtotal'))
            if d.get('id_studio'):
                mulai, selesai = BuktiController._jam(d.get('jam_mulai')), BuktiController._jam(d.get('jam_selesai'))
                jam = f"{mulai}-{selesai}" if mulai and selesai else "seharian"
                baris.append(BuktiController._kiri_kanan(f"{no}. Studio {d['nama_studio']}", subtotal))
                baris.append(f"     {tgl(trx['tgl_sewa'])}, jam {jam} ({d['jumlah']} jam)")
            else:
                baris.append(BuktiController._kiri_kanan(f"{no}. Alat {d['nama_alat']}", subtotal))
                baris.append(
                    f"     {d['jumlah']} buah x {rp(d.get('harga_per_hari'))} x {hari} hari"
                )
        if not detail:
            baris.append("(rincian item tidak ditemukan)")

        total = float(trx['total_biaya'] or 0)
        denda = float(trx.get('denda') or 0)
        baris += [strip, kk("Total sewa", rp(total))]
        if denda > 0:
            baris.append(kk("Denda keterlambatan", rp(denda)))
            baris.append(kk("TOTAL KESELURUHAN", rp(total + denda)))
        else:
            baris.append(kk("TOTAL", rp(total)))

        baris += [strip, "PEMBAYARAN", strip]
        pembayaran = PembayaranModel.lihatByTransaksi(id_transaksi)
        for i, p in enumerate(pembayaran):
            # pembayaran pertama = sewa; berikutnya = denda keterlambatan
            jenis = "Sewa" if i == 0 else "Denda"
            metode = p.get('metode_bayar') or '-'
            baris.append(kk(
                f"{jenis} | {metode} | {tgl(p.get('tgl_bayar'))} | {p.get('status_konfirmasi') or '-'}",
                rp(p.get('jumlah_bayar')),
            ))
        if not pembayaran:
            baris.append("(data pembayaran tidak ditemukan)")
        if trx['status_transaksi'] == 'Selesai' and denda > 0:
            baris.append(f"CATATAN: denda {rp(denda)} belum lunas.")
        elif trx['status_transaksi'] == 'Tuntas':
            baris.append("Seluruh tagihan (sewa + denda) telah lunas.")

        baris += [
            garis,
            "Simpan bukti ini sebagai tanda terima sewa.".center(BuktiController.LEBAR),
            "Terima kasih telah menyewa di ArtStudio-Rent.".center(BuktiController.LEBAR),
            garis,
        ]
        return True, baris

    @staticmethod
    def simpan_txt(baris, path):
        """Tulis bukti ke file TXT di `path`. Kembalikan (ok, pesan)."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(baris) + "\n")
            return True, f"Bukti sewa tersimpan di:\n{path}"
        except OSError as e:
            return False, f"Gagal menyimpan file: {e}"