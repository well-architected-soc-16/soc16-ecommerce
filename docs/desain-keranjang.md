# Desain 3.02 Keranjang + 3.03 Keranjang kosong (issue #35)

Sumber: Figma "3 · Rancangan customer" → 3.02, 3.03, dan flash di 3.01. Gaya sama dengan halaman lain
(komponen di `templates/components/`, hitam-putih, aksen #1D2128, judul kapital tebal, sudut membulat, footer lengkap).
Tabel yang dipakai sudah ada: `carts` (satu per user, `user_id` UNIQUE) dan `cart_items`
(`product_size_id` CASCADE, `quantity > 0`, UNIQUE `cart_id + product_size_id`). **Tidak ada perubahan database.**

## 1. Tambah ke keranjang (dari detail 3.01)

- Tombol "TAMBAH KE KERANJANG" di detail sekarang **aktif**. Form POST + CSRF ke `/keranjang/tambah` berisi:
  `product_size_id` (dari radio ukuran yang dipilih — ubah nilai radio menjadi id `product_sizes`, label tetap "42"),
  `quantity` (dari stepper), `next` (halaman detail).
- Tanpa ukuran dipilih → kembali ke detail dengan pesan "Pilih ukuran dulu." (validasi server, bukan hanya JS).
- Tamu → ke halaman Masuk dengan `next` kembali ke detail (lewat `safe_next`). Admin → tombol disembunyikan; kalau dipaksa POST → 403 + audit `access_denied`.
- Server memeriksa: ukuran ada, produknya aktif, stok > 0, `1 ≤ quantity ≤ stok`. Kalau item ukuran itu sudah ada di keranjang, jumlahnya **ditambah**, dibatasi stok
  (pesan: "Jumlah disesuaikan dengan stok (tersisa 3)").
- Berhasil → tetap di halaman detail dengan flash hijau seperti Figma 3.01: `'Air Jordan 1 Retro High OG …' masuk ke keranjang.`
- Keranjang (`carts`) dibuat saat item pertama ditambahkan; tangani `IntegrityError` (dua request bersamaan).
- Tombol "+ KERANJANG" di Wishlist saya (3.16): karena ukuran belum dipilih, tetap menuju halaman detail produk (anchor ke pilihan ukuran).

## 2. Header

- Ikon keranjang (tas) di header aktif untuk customer, menuju `/keranjang`.
- **Badge** bulat hitam kecil di pojok kanan atas ikon berisi **jumlah baris produk** di keranjang (sama dengan "2 produk" di judul). Tidak tampil jika 0.
  Ambil dalam satu query per request (simpan di `g`, seperti `wishlist_ids`).
- Tamu: ikon menuju Masuk. Admin: ikon tidak ditampilkan.

## 3. Halaman Keranjang 3.02 (`/keranjang`, wajib login, hanya customer)

- Judul `KERANJANG` + teks kecil abu di sebelahnya: "2 produk".
- **Dua kolom** (kiri ±65%, kanan ±35%; di HP menumpuk, ringkasan di bawah):
- **Kiri — daftar item**, dipisah garis tipis antar item. Tiap item:
  - Kotak foto kecil (±96px, sudut membulat, abu muda, "Belum ada gambar" kecil bila kosong) → tautan ke detail.
  - Nama produk (tebal, tautan ke detail).
  - Baris kecil abu: `Ukuran: EU 42`, lalu nama brand, lalu `Rp 2.149.000 / pasang`.
  - Stepper jumlah pil `– 1 +` (komponen stepper yang sama dengan detail) + tautan merah kecil `Hapus`.
    Ubah jumlah = form POST ke `/keranjang/<item_id>/ubah` (tombol – dan + mengirim form; tanpa JS tetap jalan).
    Hapus = form POST ke `/keranjang/<item_id>/hapus`.
  - Kanan item: label kecil abu `Subtotal` dan di bawahnya angka tebal `Rp 2.149.000` (harga × jumlah).
  - **Item bermasalah** (diberi kotak/teks merah kecil di bawah baris info):
    - produk disembunyikan admin → "Produk tidak tersedia lagi. Hapus dari keranjang." (stepper nonaktif);
    - stok ukuran 0 → "Stok habis";
    - jumlah > stok → "Stok tersisa 3" (jumlah **tidak** diubah diam-diam; user yang menyesuaikan).
- Di bawah daftar: tautan `← Lanjut belanja` ke `/produk`.
- **Kanan — kartu RINGKASAN** (latar abu sangat muda, sudut membulat, padding lega):
  - Judul `RINGKASAN`.
  - `Subtotal (3 barang)` ↔ `Rp 4.729.000` (3 = total jumlah pasang).
  - `Ongkos kirim` ↔ `Dikonfirmasi admin`.
  - Garis, lalu `Total` ↔ angka besar tebal `Rp 4.729.000`.
  - Tombol hitam pil lebar penuh `LANJUT KE CHECKOUT →`. Di issue ini checkout belum ada (#37): tombol **nonaktif** dengan label
    "Lanjut ke checkout (segera hadir)". Juga nonaktif bila ada item bermasalah.
  - Catatan kecil abu: "Harga & stok dicek ulang saat checkout. Keranjang hanya bisa dilihat pemiliknya."
- Harga **selalu** diambil dari `products.price` saat ini (keranjang tidak menyimpan harga).

## 4. Keranjang kosong 3.03

- Judul `KERANJANG`, lalu kartu besar abu muda di tengah: ikon troli garis, judul `KERANJANGMU MASIH KOSONG`,
  teks "Cari sepatu favoritmu dan tambahkan ke keranjang.", tombol hitam `LIHAT KATALOG →` ke `/produk`.

## 5. Aturan & keamanan

- Semua aksi POST + CSRF; semua query keranjang selalu `cart.user_id == g.user.id` → item milik orang lain = 404 (tidak ada IDOR).
- `quantity` divalidasi bilangan bulat 1–stok (tolak 0, negatif, huruf, angka raksasa); `product_size_id` harus ada dan aktif.
- Harga tidak pernah diambil dari form.
- Query tanpa N+1 (`selectinload` item → ukuran → produk → brand).
- Audit log tidak perlu untuk keranjang, kecuali admin yang mencoba (`access_denied`).
- `next` hanya lewat `safe_next()`.
