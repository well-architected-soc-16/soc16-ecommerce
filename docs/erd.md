# ERD — E-Commerce srv-web (PBL RKS-316)

Dokumen desain basis data aplikasi e-commerce Flask.
DBMS: PostgreSQL (dev: lokal WSL → produksi: srv-db 10.40.0.10, VLAN 40).

---

## 1. Diagram

```mermaid
erDiagram
    users ||--o{ orders : "memesan"
    users ||--o| carts : "memiliki"
    users ||--o{ audit_logs : "menghasilkan"
    categories ||--o{ products : "mengelompokkan"
    products ||--o{ cart_items : "ada di"
    products ||--o{ order_items : "tercatat di"
    carts ||--o{ cart_items : "berisi"
    orders ||--o{ order_items : "berisi"
    orders ||--o| payments : "dibayar via"

    users {
        int id PK
        string email UK "disimpan lowercase"
        string password_hash
        string nama
        string role "customer | admin"
        bool is_active
        int failed_login_count
        datetime locked_until "null jika tidak terkunci"
        datetime created_at
    }

    categories {
        int id PK
        string nama
        string slug UK
    }

    products {
        int id PK
        int category_id FK
        string nama
        string slug UK
        text deskripsi
        numeric harga "numeric(12,2)"
        int stock "sumber kebenaran stok"
        string image_filename "nama file hasil secure_filename"
        bool is_active
        datetime created_at
    }

    carts {
        int id PK
        int user_id FK "unik, 1 user 1 keranjang aktif"
        datetime updated_at
    }

    cart_items {
        int id PK
        int cart_id FK
        int product_id FK
        int quantity "> 0"
    }

    orders {
        int id PK
        int user_id FK
        string order_number UK
        string status "pending|paid|shipped|done|cancelled"
        numeric total_amount "dihitung ulang di server"
        text alamat_kirim
        datetime created_at
    }

    order_items {
        int id PK
        int order_id FK
        int product_id FK
        string product_nama "snapshot saat checkout"
        numeric unit_price "snapshot harga saat checkout"
        int quantity
        numeric subtotal
    }

    payments {
        int id PK
        int order_id FK "unik"
        string metode
        string proof_filename "bukti bayar, divalidasi MIME + 2MB"
        numeric amount
        string status "menunggu|terverifikasi|ditolak"
        int verified_by FK "admin yang memverifikasi"
        datetime uploaded_at
    }

    audit_logs {
        int id PK
        int user_id FK "null untuk login gagal"
        string action "login_gagal|login_sukses|akses_admin|upload|ubah_produk"
        string ip_address "dari X-Forwarded-For via ProxyFix"
        text detail
        datetime created_at
    }
```

---

## 2. Keputusan desain penting

| Keputusan | Alasan |
|---|---|
| `order_items` menyimpan **snapshot** `product_nama` + `unit_price` | Kalau harga produk berubah/dihapus, riwayat pesanan lama tidak ikut berubah. Tanpa ini, nota pelanggan bisa berubah sendiri. |
| `total_amount` **dihitung ulang di server** saat checkout | Harga dan subtotal yang dikirim browser tidak pernah dipercaya (perbaikan dari Modul 3). |
| `products.stock` satu-satunya sumber stok, dikurangi **saat checkout** di dalam transaksi | Mencegah stok minus saat dua user checkout bersamaan. Pakai `SELECT ... FOR UPDATE`. |
| `harga` pakai `numeric(12,2)`, bukan `float` | `float` menimbulkan error pembulatan pada uang. |
| `users.email` disimpan lowercase + `UNIQUE` | PostgreSQL case-sensitive; tanpa ini `A@mail.com` dan `a@mail.com` jadi dua akun. |
| `failed_login_count` + `locked_until` di tabel `users` | Pembatasan brute force yang bertahan antar worker Gunicorn (rate limiter dict di Modul 6 tidak shared). |
| `role` sebagai kolom, dicek di middleware | Dasar pemeriksaan hak akses admin (cegah IDOR / akses admin oleh customer). |
| Tabel `audit_logs` terpisah | Sumber event untuk agen Wazuh ke soc-siem: login gagal, akses admin, upload. |
| `cart_items` unik per (`cart_id`, `product_id`) | Tambah produk yang sama menambah quantity, bukan baris baru. |

---

## 3. Indeks yang perlu dibuat

- `users(email)` — UNIQUE, dipakai tiap login
- `products(slug)` — UNIQUE, untuk URL detail produk
- `products(category_id)` — filter katalog
- `orders(user_id, created_at)` — riwayat pesanan user
- `order_items(order_id)` — tampil detail pesanan
- `audit_logs(created_at)` — pencarian log per rentang waktu

---

## 4. Catatan migrasi

- Semua perubahan skema lewat Flask-Migrate: `flask db migrate -m "..."` → `flask db upgrade`
- Jangan ubah tabel langsung lewat `psql` — skema di srv-db nanti dibangun dari folder `migrations/`
