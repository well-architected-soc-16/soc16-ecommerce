# Spesifikasi Desain — Beranda (Figma 1.01–1.03)

Sumber: Figma page *Tampilan Web*, frame `9:1226` "1.01 Beranda — tamu" (1.02 = menu Brand terbuka, 1.03 = customer + menu akun terbuka → sudah dicakup komponen #26).
Semua komponen dasar (header, kartu produk, tombol pill, footer, tombol WA) sudah ada dari PR #27 — **pakai ulang**, jangan dibuat baru.

Urutan bagian (lebar konten 1280px, padding samping 16px; jarak antar bagian **56px**, sebelum "Belanja aman" **64px**):

## 1. Hero carousel
- Wrapper: padding atas 24px.
- Slide: tinggi **480px**, `rounded-[16px]`, border `#d4d4d4`, latar `#f5f5f5` (bila foto kosong), padding 40px 80px, isi rata tengah vertikal.
- Foto banner (dari `static/img/banner/`, opsional) memenuhi slide, **ditimpa gradien gelap**: `linear-gradient(to right, rgba(0,0,0,.6), rgba(0,0,0,.25) 55%, transparent)`.
- Isi slide (lebar 448px):
  - Label: pill **putih**, padding 4px 12px, Barlow Condensed Bold 12px `ink` UPPERCASE tracking 0.6px.
  - jarak 12px → Judul: Barlow Condensed ExtraBold **60px**, line-height 60px, **putih**, UPPERCASE.
  - jarak 12px → Teks: Barlow **Italic 24px**, line-height 32px, `#e5e5e5`.
  - jarak 24px → Tombol: **pill putih** (padding 12px 28px, gap 16px), Barlow Condensed Bold 16px `ink` tracking 0.8px + panah gelap 32×12 (`arrow-ink.svg`).
- Titik slide: kanan bawah, untuk **5 slide**. Pertahankan tombol ‹ › dan `carousel.js` yang ada.
- Isi 5 slide: lihat `SLIDES` di `routes/shop.py` (tambah 2 slide; tautan pakai `url_for`). Teks slide harus sesuai fitur yang benar-benar ada.

## 2. Belanja per brand
- Judul seksi (dipakai semua seksi): baris `justify-between items-end`; judul Barlow Condensed ExtraBold **30px** (lh 36px) `ink` UPPERCASE tracking 0.75px; subjudul opsional Barlow 14px `#525252` (jarak 2px); tautan kanan Barlow Condensed Bold 14px UPPERCASE tracking 0.7px **bergaris bawah**. Jarak judul → isi 16px.
- Judul "BELANJA PER BRAND", tautan "SEMUA BRAND →" (ke katalog).
- Isi: baris **7 kotak sama lebar** (gap 12px), tinggi **72px**, putih, border `#e5e5e5`, `rounded-[12px]`, nama brand rata tengah Barlow Condensed Bold 16px UPPERCASE tracking 0.8px. Hover: latar `#f5f5f5`.
- Data: brand dengan produk aktif terbanyak, maks. 7. Link ke katalog `?brand=<slug>`. HP: geser horizontal.

## 3. Rak produk geser (macro yang dipakai 3 seksi)
- Area tampil 1248px, kartu lebar **224px**, gap 16px, `overflow-x-auto` + scroll-snap, **tanpa scrollbar terlihat**.
- Tombol geser ‹ › : lingkaran 40px, latar `rgba(255,255,255,.9)`, border `#e5e5e5`, bayangan `0 1px 3px rgba(0,0,0,.1)`, teks 22px `ink`; kiri di −16px, kanan di ujung kanan, atas 88px. Sembunyikan tombol saat sudah di ujung; di HP tombol disembunyikan (geser jari).
- Kartu = macro `product_card` dari PR #27 (tanpa wishlist).
- Maks. 10 kartu per rak.

| Seksi | Judul / subjudul | Data | Tautan kanan |
|---|---|---|---|
| Produk terbaru | "PRODUK TERBARU" | produk aktif, `created_at` terbaru | "LIHAT SEMUA →" katalog |
| Produk terlaris | "PRODUK TERLARIS" / "Paling banyak dibeli bulan ini" | jumlah `order_items.quantity` dari pesanan berstatus paid/shipped/completed 30 hari terakhir. **Sembunyikan seksi bila belum ada penjualan.** | "LIHAT SEMUA →" katalog |
| Pilihan minggu ini | "PILIHAN MINGGU INI" / "Dikurasi admin Pururuna" | produk aktif `is_featured = true`. Sembunyikan bila kosong. | "LIHAT SEMUA →" katalog |

## 4. Jelajahi koleksi (4 kotak)
- Judul "JELAJAHI KOLEKSI" (tanpa tautan).
- 4 kotak sama lebar, gap 16px, tinggi **380px**, `rounded-[16px]`, border `#d4d4d4`, padding 24px, isi rata **bawah**, latar foto (opsional) + lapisan `rgba(0,0,0,.4)` (tanpa foto: `#f5f5f5` + lapisan).
- Isi: judul Barlow Condensed ExtraBold 30px putih UPPERCASE; deskripsi Barlow 14px `#e5e5e5`; jarak 6px; "LIHAT →" Barlow Condensed Bold 14px putih bergaris bawah. Seluruh kotak = satu link.

| Kotak | Deskripsi | Link (filter katalog — diproses di issue Katalog 1.04) |
|---|---|---|
| Top 50 sepatu | Paling dicari minggu ini | katalog `?urut=terlaris` (sementara terbaru) |
| Sepatu lari | Ringan untuk latihan harian | katalog `?jenis=running` |
| Di bawah Rp 1 juta | Hemat tanpa kompromi | katalog `?harga_maks=1000000` |
| Edisi terbatas | Stok sedikit, cepat habis | katalog `?stok=terbatas` |

## 5. Belanja aman di Pururuna
- Kotak latar `#f5f5f5`, `rounded-[16px]`, padding 48px 40px, gap 32px.
- Judul "BELANJA AMAN DI PURURUNA" + tautan "BACA KEBIJAKAN LENGKAP →" (ke halaman kebijakan; sementara `#` bila belum ada).
- 4 poin sama lebar (gap 32px): ikon 28px → jarak 4px → judul Barlow Condensed Bold 16px UPPERCASE tracking 0.8px `ink` → teks Barlow 14px lh 23px `#525252`:
  1. **Pembayaran diverifikasi** — Admin mengecek setiap bukti bayar. Harga yang tampil adalah harga yang kamu bayar.
  2. **Akun terlindungi** — Akun terkunci otomatis setelah beberapa kali salah password.
  3. **Tukar ukuran 3 hari** — Penukaran ukuran maksimal 3 hari setelah barang diterima, kondisi utuh. *(kebijakan perlu dikonfirmasi tim)*
  4. **Privasi terjaga** — Kami hanya menyimpan nama, email, dan alamat. Password disimpan dalam bentuk hash.

## 6. Footer lengkap + tombol WhatsApp
Sudah ada dari PR #27 (WA hanya di beranda, hanya bila `WA_TOKO` diisi).

## Dihapus dari beranda lama
- Seksi "Stok terbatas" (diganti kotak "Edisi terbatas").
- Grid "Semua produk" + chip brand + pagination → **pindah ke `/produk`** (halaman katalog). `/produk` tidak lagi redirect ke beranda.
- Seksi "Kenapa belanja" lama (diganti "Belanja aman").

## Tampilan HP (≤ 768px)
Hero tinggi ±360px, judul 40px, padding 24px; kotak brand & rak = geser horizontal; 4 kotak koleksi jadi 2 kolom (tinggi 220px); 4 poin "Belanja aman" jadi 1–2 kolom.

## Ikon baru (URL Figma, berlaku 7 hari) → `static/icons/`
- `shield-check` (pembayaran): https://www.figma.com/api/mcp/asset/10ec3536-aeb1-468a-bc96-947c7a08fc7b/12ed2.svg
- `lock` (akun): https://www.figma.com/api/mcp/asset/10ec3536-aeb1-468a-bc96-947c7a08fc7b/5c70d.svg
- `swap` (tukar ukuran): https://www.figma.com/api/mcp/asset/10ec3536-aeb1-468a-bc96-947c7a08fc7b/6b024.svg
- `privacy` (privasi): https://www.figma.com/api/mcp/asset/10ec3536-aeb1-468a-bc96-947c7a08fc7b/6152d.svg
- panah gelap untuk tombol putih: https://www.figma.com/api/mcp/asset/10ec3536-aeb1-468a-bc96-947c7a08fc7b/48db0.svg (atau pakai `arrow-ink.svg` yang sudah ada)
