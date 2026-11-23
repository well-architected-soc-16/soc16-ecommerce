# CLAUDE.md — Konteks proyek untuk Claude Code

Aplikasi e-commerce **Pururuna** (toko sepatu) untuk PBL RKS-316 "Well Architected SOC 16".
Berjalan di **srv-web (DMZ)**, database di **srv-db** (PostgreSQL). Tim lain memantau log aplikasi lewat Wazuh (SOC).

## Pembagian peran

- **Claude Code**: menulis dan mengubah kode di repo ini (backend, model, route, form, template sesuai instruksi).
- **Desain tampilan TIDAK ditentukan di sini.** Acuan desain ada di Figma dan dikirim terpisah per fitur.
  Jangan mendesain ulang tampilan atas inisiatif sendiri; kalau membuat template baru, ikuti gaya yang sudah ada
  (hitam-putih, Tailwind CDN, font Barlow / Barlow Condensed).
- **Developer (manusia)**: menjalankan migrasi, menguji di browser, commit, push, dan membuat PR.
  **Jangan commit atau push.**

## Stack

Flask 3 (app factory + blueprint), Flask-SQLAlchemy 3 / SQLAlchemy 2 (gaya `db.select`), Flask-Migrate (Alembic),
Flask-WTF (CSRF), Jinja2, PostgreSQL 16 (driver `psycopg` 3), Gunicorn di belakang Nginx (produksi).
Dev: WSL Ubuntu, database `ecommerce`, user `ecom` (bukan superuser).

## Struktur

```
app.py            create_app(), filter template (rupiah, wib)
config.py         Config dari .env (SECRET_KEY & DATABASE_URL wajib)
extensions.py     db (dengan naming_convention), migrate, csrf
audit.py          catat(event, user=None, email=None, **detail) → DB + file JSON (dibaca Wazuh)
utils.py          buat_slug, slug_unik
commands.py       flask buat-admin, flask seed
models/           user, product (Brand, ProductGroup, Product, ProductSize), cart, order (Order, OrderItem, Payment), audit_log
routes/           auth (tanpa prefix), admin (/admin), shop (tanpa prefix, termasuk "/")
forms/            auth, admin
templates/        Jinja2
docs/             erd.md + erd.png (skema v2), fitur.md (13 fitur + layar Figma)
```

## Acuan wajib

- **Skema database: `docs/erd.md`.** Model harus selalu sama dengan ERD. Kalau model diubah, ERD ikut diperbarui.
- **Daftar fitur & urutan: `docs/fitur.md`.**
- **Alur kerja tim: `CONTRIBUTING.md`.**

## Konvensi penamaan

- Tabel, kolom, nama fungsi, variabel Python, key `detail` audit log, dan **nilai status**: **bahasa Inggris** (snake_case).
- **URL dan semua teks yang dilihat pengguna: bahasa Indonesia** (`/produk`, `/admin/brand`, "Stok habis").
- Nilai status diterjemahkan di template, contoh `pending_payment` → "Menunggu bayar".
- Whitelist nilai (ROLES, AUDIENCES, PRODUCT_TYPES, ORDER_STATUSES, PAYMENT_STATUSES, PAYMENT_METHODS) didefinisikan
  sekali di `models/` dan dipakai ulang untuk CHECK constraint (`sql_in`), pilihan form, dan validasi filter.
- Nama constraint jangan ditulis manual lengkap; `naming_convention` di `extensions.py` yang membentuknya
  (cukup `db.CheckConstraint("price >= 0", name="price")`).
- Waktu disimpan UTC (`now_utc()` dari `models`), ditampilkan WIB lewat filter `|wib`.

## Aturan keamanan (wajib di setiap fitur)

- **Otorisasi admin** hanya lewat `@admin_bp.before_request require_admin`. Jangan buat decorator admin kedua.
  Akses ditolak dicatat `access_denied`.
- **Cek kepemilikan (IDOR)**: data milik user (keranjang, pesanan, bukti bayar) selalu difilter `user_id == g.user.id`.
- **Harga, subtotal, total dihitung ulang di server.** Jangan pernah memakai harga dari form/browser.
- **Stok** hanya di `product_sizes.stock`; dikurangi saat checkout dalam satu transaksi dengan `SELECT ... FOR UPDATE`;
  dikembalikan saat pesanan dibatalkan.
- **Snapshot** nama, ukuran, warna, harga ke `order_items` saat checkout.
- **Upload file** (bukti bayar, gambar produk): cek ekstensi + MIME (`puremagic`) + `secure_filename` + maks 2 MB,
  simpan dengan nama acak **di luar folder static/web root**, sajikan lewat route yang cek hak akses.
- **Upload ulang bukti bayar** setelah ditolak: **update baris `payments` yang sama** (`order_id` UNIQUE), jangan buat baris baru.
- **Input query** (filter, urutan, pencarian) divalidasi dengan whitelist; pencarian pakai `icontains(..., autoescape=True)`.
- **Output** selalu lewat template Jinja (autoescape). Jangan return f-string berisi data user. Jangan pakai `|safe` untuk data user.
- **Semua form pakai CSRF** (Flask-WTF). Aksi yang mengubah data wajib POST.
- **Password**: hash Werkzeug; tidak pernah dicatat di log/audit; login gagal pakai `DUMMY_HASH` untuk menyamakan waktu respons.
- **Penguncian akun** disimpan di `users.failed_login_count` + `locked_until` (bukan di memori), supaya berlaku di semua worker Gunicorn.
- **Ganti password/email admin hanya lewat CLI server**, bukan form web. Customer boleh ganti password (minta password lama).
- **Hapus akun = anonimisasi**: email → `deleted-{id}@deleted.invalid`, name → "Akun dihapus", phone/address → NULL,
  password diacak, `is_active=False`, keranjang dihapus. Baris user dan pesanannya tetap ada.
- **Halaman error** (404/403/500) tidak menampilkan stack trace.
- **Jangan hardcode rahasia atau data pribadi** (nomor HP, password, key) di kode. Semua lewat `.env`.
- `TRUST_PROXY=1` hanya kalau berjalan di belakang Nginx (ProxyFix untuk IP asli di audit log).

## Audit log

- Panggil `catat("event_name", user=..., **detail)` untuk aksi penting. Event & key detail bahasa Inggris.
- Event yang sudah ada: `register`, `register_failed`, `login_success`, `login_failed`, `account_locked`, `logout`,
  `access_denied`, `brand_created/updated/deleted`, `product_created/updated/shown/hidden/deleted`.
- Nilai `reason`: `wrong_password`, `unknown_email`, `account_locked`, `account_inactive`, `email_taken`.
- Format baris JSON di file log **jangan diubah** tanpa koordinasi dengan tim SOC (dipakai rule Wazuh).

## Keputusan yang sudah diambil

- Filter & urutan katalog (brand, harga, ukuran, warna, untuk, jenis) **ditunda**; dikerjakan bersama tampilan katalog dari Figma.
- `product_groups` dibatasi per brand (`brand_id`); varian warna = produk dengan `group_id` sama.
- Ukuran memakai EU 2 digit (30–50); urutan string aman untuk rentang ini.
- Retensi audit log 90 hari (perintah `flask hapus-log-lama`) **belum dibuat**.
- Lupa password customer butuh SMTP → **belum dibuat**.

## Perintah

```bash
flask --app app run --debug           # dev saja, JANGAN --debug di server
flask --app app db migrate -m "..."   # setelah ubah model
flask --app app db upgrade
flask --app app seed                  # data contoh (hanya jika tabel produk kosong)
flask --app app buat-admin
```

Jangan ubah tabel langsung lewat `psql`; semua perubahan skema lewat migrasi.

## Git

- Satu issue = satu branch (`feat/`, `fix/`, `refactor/`, `docs/`, `chore/`), dibuat dari `main`.
- PR berisi `Closes #<issue>` dan `Refs #7`. Push langsung ke `main` diblokir.
- **Jangan pernah** commit `.env`, `logs/`, gambar produk/banner berhak cipta (`static/img/*`), `*.session.sql`, `*:Zone.Identifier`.
- Developer menambahkan file satu per satu (`git add <file>`), bukan `git add .`.

## Saat menyelesaikan tugas

Laporkan: daftar file yang berubah, apa yang sudah dicek, dan apa yang perlu diuji developer di PostgreSQL/browser.
