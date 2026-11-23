# 13 Kebutuhan Fungsional — E-Commerce Pururuna (PBL RKS-316) · v2

Daftar final fitur aplikasi, acuan untuk RPP, ERD (`erd.md` v2), dan urutan pengerjaan.
Acuan tampilan: Figma "Pururuna — Dashboard Admin" (nomor layar ditulis di kolom **Layar**).
Kolom **Kerjakan**: *sendiri* = ditulis manual (titik keamanan, harus bisa dipertanggungjawabkan saat demo).

---

## A. Sisi Customer (7 fitur)

| # | Fitur | Isi | Tabel | Layar | Kontrol keamanan | Kerjakan |
|---|---|---|---|---|---|---|
| 1 | Register akun | Form daftar, validasi email & password policy | `users` | 1.09–1.10 | Hash password (Werkzeug), email lowercase + UNIQUE, CSRF, validasi di browser (HTML5) **dan** di server, pesan error tidak membocorkan struktur DB | **sendiri** |
| 2 | Login, logout & profil | Masuk/keluar, ubah nama/HP/alamat, ganti password (customer) | `users`, `audit_logs` | 1.06–1.08, 1.12, 3.08–3.09 | `session.clear()` saat login, penguncian akun (`failed_login_count` + `locked_until`), logout wajib POST, ganti password minta password lama; **admin tidak bisa ganti password/email lewat web** (hanya CLI server) | **sendiri** |
| 3 | Katalog & detail produk | Daftar produk, filter brand/harga/ukuran/warna/untuk/jenis, urutan, pencarian, detail dengan pilihan ukuran & varian warna | `products`, `brands`, `product_sizes`, `product_groups` | 1.01–1.05, 3.01, 3.14 | Query lewat ORM, nilai filter & urutan divalidasi whitelist, escape output Jinja, pencarian `ilike` dengan autoescape | AI + review |
| 4 | Keranjang | Tambah (pilih ukuran), ubah qty, hapus item | `carts`, `cart_items`, `product_sizes` | 3.02–3.03 | Keranjang milik user login (cek kepemilikan, cegah IDOR), qty > 0 dan ≤ stok ukuran | AI + review |
| 5 | Checkout | Buat pesanan dari keranjang, isi data penerima | `orders`, `order_items`, `product_sizes` | 3.04 | **Harga, subtotal, total dihitung ulang di server**, stok per ukuran dikurangi dalam transaksi (`SELECT … FOR UPDATE`), nama/ukuran/warna/harga di-snapshot ke `order_items` | **sendiri** |
| 6 | Upload bukti bayar | Unggah gambar bukti transfer | `payments` | 3.05 | Validasi ekstensi + MIME (`puremagic`) + `secure_filename` + batas 2 MB, file disimpan di luar web root, hanya pemilik pesanan | **sendiri** |
| 7 | Riwayat pesanan | Daftar pesanan user + detail + cetak nota | `orders`, `order_items`, `payments` | 3.06–3.07, 3.15 | Cek kepemilikan pesanan (IDOR), nomor pesanan acak (bukan berurutan) | AI + review |

## B. Sisi Admin (6 fitur)

| # | Fitur | Isi | Tabel | Layar | Kontrol keamanan | Kerjakan |
|---|---|---|---|---|---|---|
| 8 | CRUD produk | Tambah/ubah/hapus produk, stok per ukuran, warna & grup, upload gambar | `products`, `product_sizes`, `product_groups` | 2.02–2.04 | Cek `role = admin` di setiap route, validasi upload sama dengan fitur 6, slug otomatis & unik, hapus produk tidak merusak pesanan lama (`SET NULL` + snapshot) | AI + review |
| 9 | Kelola brand | CRUD brand + logo | `brands` | 2.05–2.06 | Cek admin, hapus brand ditolak bila masih dipakai produk (`RESTRICT`) | AI + review |
| 10 | Kelola pesanan | Daftar pesanan, ubah status (`paid → shipped → completed`, atau `cancelled`) | `orders` | 4.02–4.03 | Cek admin, perpindahan status divalidasi (tidak bisa lompat), stok dikembalikan saat dibatalkan, dicatat ke `audit_logs` | AI + review |
| 11 | Verifikasi pembayaran | Lihat bukti bayar, terima/tolak dengan alasan | `payments`, `orders` | 4.04–4.05 | Cek admin, `verified_by` + `verified_at` dicatat, status pesanan ikut diperbarui dalam satu transaksi, bukti bayar hanya bisa dibuka admin & pemilik | AI + review |
| 12 | Kelola user | Aktif/nonaktifkan, buka kunci login, hapus akun (anonimisasi: data pribadi dikosongkan, riwayat pesanan tetap) | `users` | 4.06–4.07 | Cek admin, admin tidak bisa menonaktifkan/menghapus dirinya sendiri, hapus akun minta konfirmasi, semua aksi dicatat ke `audit_logs` | **sendiri** |
| 13 | Lihat audit log | Daftar aktivitas penting, filter per event & rentang waktu | `audit_logs` | 2.07 | Cek admin, log read-only (tidak bisa dihapus lewat UI), retensi 90 hari lewat CLI (`flask hapus-log-lama`), password tidak pernah dicatat | **sendiri** |

## C. Pendukung (dari desain Figma)

| Fitur | Isi | Layar | Catatan |
|---|---|---|---|
| Dashboard admin (hub) | Kartu statistik + pratinjau tiap fitur admin, tanpa sidebar | 4.01 | Dibuat setelah fitur 8–13 ada datanya |
| Laporan transaksi | Rekap per periode + export CSV | 4.08 | Data dari `orders` berstatus `paid` ke atas |
| Profil admin | Hanya baca | 4.09 | Ganti password admin lewat `flask --app app ganti-password-admin <email>` |
| Halaman kebijakan | Privasi, keamanan transaksi, pengembalian, log aktivitas | 3.10 | Teks harus sesuai fitur yang benar-benar jalan |
| Halaman error | 404, 403, 500 | 3.11–3.13 | Tanpa stack trace; tampilkan kode kejadian yang bisa dicari di log server |
| Tampilan HP | Semua halaman customer | 6.01–6.06 | Dikerjakan bersama tiap fitur, bukan fitur terpisah |

## D. Tambahan (issue #30)

Di luar 13 fitur utama. Skema (`reviews`, `wishlist_items`) sudah dibuat di #30; route & tampilan menyusul.

| # | Fitur | Isi | Tabel | Layar | Kontrol keamanan | Kerjakan |
|---|---|---|---|---|---|---|
| 14 | Ulasan & rating — **FR-005** (kertas penilaian dosen: melihat & menulis ulasan/rating) | Lihat ulasan + rata-rata rating di detail produk; customer menulis/mengubah ulasannya sendiri (rating 1–5, komentar maks 1000 karakter) | `reviews`, `orders`, `order_items` | 3.01 | Hanya user login; usulan (perlu konfirmasi tim): **hanya pembeli** (punya pesanan `completed` berisi produk itu, simpan `order_id`); satu ulasan per user per produk (UNIQUE); ubah/hapus hanya milik sendiri (IDOR); komentar lewat Jinja autoescape, tanpa `|safe`; CSRF + POST | AI + review |
| 15 | Wishlist | Tombol ♡ di kartu & detail produk, ikon ♡ di header, halaman "Wishlist saya" | `wishlist_items` | komponen #26 (ikon header, tombol kartu, menu akun) | Hanya user login (tamu diarahkan ke Masuk); tambah/hapus wajib POST + CSRF; daftar difilter `user_id == g.user.id` (IDOR); UNIQUE mencegah baris ganda; produk nonaktif tidak ditampilkan | AI + review |

---

## Catatan desain

- **Semua nama tabel, kolom, dan nilai status berbahasa Inggris** (lihat `erd.md` v2). Teks yang dilihat pengguna tetap bahasa Indonesia.
- **Status pesanan:** `pending_payment → awaiting_verification → paid → shipped → completed`, atau `cancelled`.
- **Stok disimpan per ukuran** di `product_sizes`; stok total produk dihitung, tidak disimpan.
- **Warna produk = 17 nilai tetap** (`COLORS` di `models/product.py`, kunci Inggris + label Indonesia + hex bulatan), dipakai form admin, filter katalog, dan CHECK.
- **Ukuran EU bulat atau .5** (30–50, mis. `40.5`), diurutkan sebagai angka; konversi ke US/UK hanya perkiraan lewat fungsi `convert_size` (tanpa tabel DB).
- **Fitur 13 adalah jembatan ke SOC.** Event yang sama dikirim agen Wazuh ke soc-siem (VLAN 30). Format log disepakati dengan anggota tim SOC.
- **IP di `audit_logs`** diambil lewat ProxyFix + `X-Forwarded-For` (`TRUST_PROXY=1` hanya di belakang Nginx).
- **Penguncian login disimpan di tabel `users`**, bukan di memori, supaya berlaku di semua worker Gunicorn.
- **Belum termasuk:** lupa password customer (butuh SMTP, tabel `password_reset_tokens`).

## Urutan pengerjaan

1. Rombak skema v2 + perbaiki fitur yang sudah ada (1–3, 8–9, 13) agar jalan di skema baru
2. Fitur 4–5 (keranjang & checkout)
3. Fitur 6, 11 (bukti bayar & verifikasi) — satu alur
4. Fitur 7, 10 (riwayat & kelola pesanan)
5. Fitur 12 (kelola user)
6. Pendukung: dashboard hub, laporan, halaman error
7. Tambahan #30: Ulasan (14) bersama detail produk 3.01; Wishlist (15) setelah fitur login/profil stabil

Satu issue per fitur, uji keamanan tiap fitur, lalu buat catatan masalah & catatan langkah.
