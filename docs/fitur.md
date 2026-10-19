# 13 Kebutuhan Fungsional — E-Commerce srv-web (PBL RKS-316)

Daftar final fitur aplikasi, acuan untuk RPP, ERD, dan urutan pengerjaan.
Kolom **Kerjakan** menandai pembagian kerja: *sendiri* = ditulis manual (titik keamanan, harus bisa dipertanggungjawabkan saat demo).

---

## A. Sisi Customer (7 fitur)

| # | Fitur | Isi | Tabel | Kontrol keamanan | Kerjakan |
|---|---|---|---|---|---|
| 1 | Register akun | Form daftar, validasi email & password policy | `users` | Hash password (Werkzeug), email disimpan lowercase + UNIQUE, CSRF, pesan error tidak membocorkan struktur DB | **sendiri** |
| 2 | Login, logout & profil | Masuk/keluar, ubah data diri, ganti password | `users`, `audit_logs` | `session.clear()` saat login, pembatasan percobaan (`failed_login_count` + `locked_until`), logout wajib POST, ganti password minta password lama | **sendiri** |
| 3 | Katalog & detail produk | Daftar produk, filter kategori, pencarian, halaman detail | `products`, `categories` | Query parameter difilter (cegah SQL injection lewat ORM), escape output Jinja, pencarian pakai `ilike` | AI + review |
| 4 | Keranjang | Tambah, ubah qty, hapus item | `carts`, `cart_items` | Keranjang milik user login (cek kepemilikan, cegah IDOR), qty divalidasi > 0 | AI + review |
| 5 | Checkout | Buat pesanan dari keranjang | `orders`, `order_items`, `products` | **Harga & subtotal dihitung ulang di server**, stok dikurangi dalam transaksi (`SELECT … FOR UPDATE`), harga & nama di-snapshot ke `order_items` | **sendiri** |
| 6 | Upload bukti bayar | Unggah gambar bukti transfer | `payments` | Validasi ekstensi + MIME (`puremagic`) + `secure_filename` + batas 2 MB, file disimpan di luar web root | **sendiri** |
| 7 | Riwayat pesanan | Daftar pesanan user + detail | `orders`, `order_items` | Cek kepemilikan pesanan (IDOR), nomor pesanan tidak berurutan tebakan | AI + review |

## B. Sisi Admin (6 fitur)

| # | Fitur | Isi | Tabel | Kontrol keamanan | Kerjakan |
|---|---|---|---|---|---|
| 8 | CRUD produk | Tambah/ubah/hapus produk + upload gambar | `products` | Middleware cek `role = admin`, validasi upload sama dengan fitur 6, slug dibuat otomatis & unik | AI + review |
| 9 | Kelola kategori | CRUD kategori | `categories` | Middleware admin, hapus kategori ditolak bila masih dipakai produk (`RESTRICT`) | AI + review |
| 10 | Kelola pesanan | Ubah status pesanan (pending → paid → shipped → done/cancelled) | `orders` | Middleware admin, perpindahan status divalidasi (tidak bisa lompat sembarangan) | AI + review |
| 11 | Verifikasi pembayaran | Lihat bukti bayar, terima/tolak | `payments`, `orders` | Middleware admin, `verified_by` dicatat, status pesanan ikut diperbarui dalam satu transaksi | AI + review |
| 12 | Kelola user | Aktif/nonaktifkan user, reset kunci login | `users` | Middleware admin, admin tidak bisa menonaktifkan dirinya sendiri, perubahan role dicatat ke `audit_logs` | **sendiri** |
| 13 | Lihat audit log | Daftar aktivitas: login gagal/sukses, akses admin, upload, ubah produk — filter per aksi & rentang waktu | `audit_logs` | Middleware admin, log read-only (tidak bisa dihapus lewat UI) | **sendiri** |

---

## Catatan desain

- **Tidak ada tabel baru.** 13 fitur ini seluruhnya tertutup oleh ERD 9 tabel (`erd.md`), jadi migrasi pertama bisa langsung dibuat.
- **Fitur 13 adalah jembatan ke SOC.** Tabel `audit_logs` yang ditampilkan di sini adalah sumber event yang sama yang dikirim agen Wazuh ke soc-siem (VLAN 30). Format log perlu disepakati dengan anggota tim SOC.
- **IP di `audit_logs`** harus diambil lewat ProxyFix + `X-Forwarded-For`; di belakang Nginx, `request.remote_addr` berisi IP Nginx, bukan IP penyerang.
- **Pembatasan login disimpan di tabel users**, bukan di memori — rate limiter berbasis dict tidak shared antar worker Gunicorn di srv-web.

## Urutan pengerjaan

1. Fitur 1–2 (akun) — fondasi, dipakai semua fitur lain
2. Fitur 3 (katalog) + fitur 8–9 (CRUD produk & kategori) — butuh data produk untuk diuji
3. Fitur 4–5 (keranjang & checkout)
4. Fitur 6–7, 10–11 (pembayaran & pesanan)
5. Fitur 12–13 (user & audit log)

Commit per fitur, uji singkat tiap fitur selesai, catat di `CATATAN.md`.
