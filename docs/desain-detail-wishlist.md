# Desain 3.01 Detail produk + 3.16/3.17 Wishlist (issue #34)

Sumber: Figma "3 · Rancangan customer" → 3.01, 3.16, 3.17. Gaya mengikuti komponen yang sudah ada
(`components/*`, hitam-putih, aksen #1D2128, font judul kapital tebal, sudut membulat).

## 3.01 Detail produk (`/produk/<slug>`)

Urutan dari atas:

1. **Flash** (komponen flash yang ada), contoh "'Air Jordan 1 …' masuk ke keranjang." (dipakai di #35).
2. **Breadcrumb**: `Beranda / <Brand> / <Nama produk>`; brand menuju katalog terfilter brand.
3. **Dua kolom** (kiri ±50% foto, kanan info):
   - Kiri: foto produk besar, sudut membulat, latar abu muda; jika kosong teks "Belum ada gambar".
   - Kanan, berurutan:
     - Chip brand (pil kecil kapital, mis. `AIR JORDAN`).
     - Nama produk: judul besar kapital tebal (2 baris boleh).
     - Rating: 5 bintang kuning + angka rata-rata (mis. `4,6`) + tautan "`23 ulasan`" (scroll ke bagian ulasan). Jika belum ada ulasan: "Belum ada ulasan".
     - Harga besar tebal `Rp 2.149.000`.
     - "Stok total: 550 pasang" (abu, kecil).
     - Deskripsi singkat (paragraf).
     - **Warna**: label "Warna: Hitam / Kuning". Di bawahnya thumbnail kotak varian (produk lain di grup model yang sama, termasuk produk ini). Thumbnail aktif berborder tebal. Di bawah tiap thumbnail titik-titik warna (1–3 titik dari `product_colors`). Varian yang stoknya 0 diberi teks kecil "Habis". Klik thumbnail → halaman detail varian itu.
     - **Pilih ukuran (EU)** + tautan kanan "Panduan ukuran" (sementara menuju halaman Kebijakan/anchor, boleh `#`). Grid tombol ukuran 8 kolom. Ukuran stok 0: teks dicoret + abu, tidak bisa dipilih. Ukuran terpilih: latar hitam teks putih. Tooltip ±US/UK tetap. Di bawah: teks kecil "Sisa 3 pasang untuk EU 42 · ukuran bergaris = stok habis" (muncul setelah ukuran dipilih, pakai JS kecil; tanpa JS cukup teks keterangan).
     - **Jumlah**: stepper `– 1 +` (min 1, maks stok ukuran terpilih).
     - Baris tombol: **TAMBAH KE KERANJANG** (lebar penuh, hitam, pil) — di issue ini masih **nonaktif** dengan label "Tambah ke keranjang (segera hadir)" sampai #35; di sebelah kanan tombol bulat **♡** (wishlist, lihat bawah).
     - Teks kecil centang: "Harga dihitung ulang saat checkout · pembayaran diverifikasi admin".
     - **Akordeon** (`<details>`): "GARANSI TUKAR UKURAN 3 HARI" (terbuka; isi: "Ukuran tidak pas? Tukar ukuran maksimal 3 hari setelah barang diterima, kondisi utuh dengan kotak & label."), "PEMBAYARAN DIVERIFIKASI ADMIN", "PENGIRIMAN & ONGKIR". Isi dua terakhir singkat, ambil dari teks yang sudah dipakai di beranda/kebijakan. **Catatan:** teks "tukar ukuran 3 hari" belum disepakati tim — tetap tampilkan sesuai Figma, tandai TODO di CLAUDE.md.
     - Baris kecil: "Brand: <tautan>  ·  Koleksi: <tautan Produk terbaru / Edisi terbatas>".
4. **TENTANG PRODUK INI** (dua kolom): kiri judul + deskripsi lengkap; kanan kartu tabel spesifikasi berbaris:
   Brand, Warna (label gabungan), Bahan (`material`), Fit (`fit`), Ukuran tersedia (mis. "EU 37 – 47", dari ukuran stok > 0), Kode (`sku`). Baris yang nilainya kosong **disembunyikan**.
5. **ULASAN PEMBELI** + dropdown kanan "Terbaru" (urut: terbaru, rating tertinggi, rating terendah):
   - Kiri atas: kartu ringkasan — angka besar `4,6` + bintang + "dari 23 ulasan", lalu 5 baris bar distribusi (5★…1★) dengan jumlah di kanan.
   - Kiri bawah: kartu **TULIS ULASAN** — di issue ini cukup tampil keterangan sesuai status:
     tamu → "Masuk untuk menulis ulasan"; sudah login tapi belum punya pesanan Selesai → "Hanya pembeli dengan pesanan berstatus Selesai yang bisa memberi ulasan. 1 ulasan per produk." Form tulis ulasan **tidak** dibuat di sini.
   - Kanan: chip filter `Semua`, `5★`, `4★`, `3★ ke bawah`, `Dengan foto` (query string, mis. `?ulasan=5`), lalu daftar ulasan: avatar inisial bulat, nama, badge hijau "✓ Pembeli terverifikasi" (jika `order_id` ada), bintang, tanggal (`12 Nov 2026`), "Ukuran EU 38" (dari `reviews.size`), komentar, thumbnail foto (dari `review_photos`, jika ada). Tampil 3 ulasan dulu, lalu tombol outline "LIHAT 20 ULASAN LAINNYA" (boleh pakai paginasi `?ulasan_hal=2`). Belum ada ulasan → teks kosong yang ramah.
   - Nama penulis tampil "Nama depan + inisial belakang" (privasi), mis. "Rina P.".
6. **WARNA LAIN DARI MODEL INI** + subjudul nama model + "LIHAT SEMUA →": rak produk (komponen `product_shelf`) berisi varian lain grup yang sama. Sembunyikan bagian jika tidak ada varian lain.
7. **PRODUK TERKAIT** + "LIHAT SEMUA →": rak produk dari brand / jenis yang sama (maks. 10, kecuali produk ini).
8. Footer.

Kartu produk di rak: tambah tombol ♡ kecil di pojok kanan atas foto (sama dengan wishlist).

## Wishlist

- **Tombol ♡** (di detail, kartu produk, rak): form POST + CSRF ke `/wishlist/<product_id>` (toggle). Ikon garis = belum disimpan, ikon terisi hitam = sudah disimpan. Tamu → redirect ke login dengan `next` kembali ke halaman asal. Setelah toggle kembali ke halaman asal (cek `next` hanya path lokal — cegah open redirect). Flash singkat "Disimpan ke wishlist" / "Dihapus dari wishlist".
- **Header**: ikon ♡ di antara "BARU" dan ikon keranjang, menuju `/wishlist`.
- **3.16 Wishlist saya (`/wishlist`)**: breadcrumb `Beranda / Wishlist saya`, judul `WISHLIST SAYA` + teks kecil "6 produk", dropdown kanan urutan "Terakhir disimpan" (opsi: terakhir disimpan, harga termurah, harga termahal). Grid 4 kolom kartu: foto (♡ terisi di pojok untuk menghapus), harga, nama, brand; jika stok total 0 → teks merah "Stok habis". Di bawah kartu tombol outline pil "+ KERANJANG" (di issue ini menuju halaman detail; diaktifkan di #35), atau tombol abu nonaktif "STOK HABIS". Catatan bawah dalam kotak abu: "Klik ♡ lagi untuk menghapus dari wishlist. Harga & stok selalu mengikuti data terbaru; produk yang disembunyikan admin tidak ditampilkan."
- **3.17 Wishlist kosong**: judul sama, kartu besar abu muda di tengah: ikon ♡ garis, judul "BELUM ADA PRODUK DISIMPAN", teks "Tekan ikon ♡ di produk yang kamu suka supaya gampang dicari lagi.", tombol hitam "LIHAT KATALOG →" ke `/produk`.

## Aturan & keamanan
- Detail: produk `is_active = false` → 404 untuk customer/tamu.
- Wishlist hanya milik user login; query selalu `WHERE user_id = current_user`. Produk tersembunyi tidak bisa ditambahkan (404) dan tidak ditampilkan di daftar.
- Toggle idempotent; tangani IntegrityError (UNIQUE) dengan aman.
- Admin boleh melihat tapi wishlist hanya untuk role customer (admin klik ♡ → 403 atau tombol disembunyikan).
- Semua query pakai `selectinload` (tanpa N+1): varian, warna, ukuran, ulasan + foto + user.
- Audit log tidak perlu untuk wishlist (bukan aksi sensitif).
