# Spesifikasi Desain — Layout Dasar & Komponen (Figma section 5)

Sumber: Figma "Pururuna — Dashboard Admin", page *Tampilan Web*, section **5 · Komponen** (node `44:2149`).
Dokumen ini ditulis dari data Figma (ukuran, warna, font persis). Stack proyek: Jinja2 + Tailwind CDN.

## 0. Token dasar

| Token | Nilai | Pemakaian |
|---|---|---|
| `ink` | `#1D2128` | teks utama, tombol utama, bar pengumuman, chip aktif |
| `ink-muda` | `#353B46` | hover tombol pill, status "Dikirim" |
| Hitam admin | `#111111` | teks & tombol di halaman admin |
| neutral | Tailwind default (`#fafafa` 50, `#f5f5f5` 100, `#e5e5e5` 200, `#d4d4d4` 300, `#a3a3a3` 400, `#737373` 500, `#525252` 600) | |
| Merah | `#b91c1c` (teks bahaya/Keluar/Stok habis), `#dc2626` (border & teks error), `#fef2f2` (latar error), `#fecaca` (border status merah) | |
| Hijau | `#16a34a` (tombol WA, border flash sukses), `#f0fdf4` latar, `#166534` teks | |
| Font | `Barlow` (400/500/600/700) untuk teks; `Barlow Condensed` (700/800) untuk judul, label UPPERCASE, tombol | sudah dimuat di base.html; tambah bobot 500 & 600 untuk Barlow |
| Lebar konten | `max-w-7xl` (1280px), padding samping 16px | |
| Radius | pill `rounded-full`; kartu `12px`; gambar `8px`; dropdown `12px` (akun) / `16px` (brand); isian `12px` | |

Tailwind config: `colors: { ink: { DEFAULT: '#1D2128', muda: '#353B46' } }`.

## 1. Bar Pengumuman (`4:24`)
- Tinggi 36px, latar `ink`, teks putih Barlow Condensed Bold 14px, UPPERCASE, tracking 0.7px, rata tengah.
- Teks: "Belanja aman · pembayaran diverifikasi admin · Fast respon".
- **Tidak tampil di halaman admin.**

## 2. Header toko (`4:70`) — 3 keadaan: Tamu / Customer / Admin
- Tinggi 60px, `sticky top-0`, latar `rgba(255,255,255,0.85)` + `backdrop-blur-[6px]`, border bawah `#e5e5e5`.
- Isi (lebar 1280, padding 12px 16px, gap 16px, rata tengah vertikal):
  1. **Logo** "PURURUNA" — Barlow Condensed ExtraBold 24px, tracking −0.6px, `ink`, link ke beranda.
  2. **Kolom cari** (flex-1) — latar `#f5f5f5`, `rounded-full`; input padding 10px 20px, Barlow 16px, placeholder "Cari produk atau brand" warna `#a3a3a3`; tombol ikon search 24px (padding 10px 16px). Fokus: border `ink`.
  3. **Menu utama** — Barlow Condensed Bold 14px, UPPERCASE, tracking 0.7px, gap 20px: "Semua", "Brand ▾" (buka dropdown Brand), "Baru".
  4. **Ikon wishlist** ♡ (kotak 36px, ikon 24px). Tamu → ke Masuk. *(lihat Catatan A)*
  5. **Ikon keranjang** (kotak 36px, ikon 26px). Customer/Admin: badge jumlah — lingkaran 18px, latar `ink`, border 1.5px putih, angka Barlow Bold 10px putih, posisi kiri 20px / atas −2px. Tamu → ke Masuk.
  6. **Tamu:** "Masuk" (Barlow Medium 14px) + tombol "DAFTAR" (pill `ink`, padding 8px 20px, Barlow Condensed Bold 14px putih, tracking 0.7px).
     **Customer/Admin:** ikon user 28px + nama (Barlow Medium 14px), padding 4px, gap 8px → membuka Menu Akun.
- HP: kolom cari turun ke baris kedua, menu utama jadi baris sendiri (seperti sekarang).

## 3. Menu Akun — dropdown (`4:93`)
- Lebar 256px, padding 6px, `rounded-[12px]`, latar `rgba(255,255,255,0.7)` + `backdrop-blur-[8px]`, border `rgba(0,0,0,0.06)`, bayangan `0 4px 3px rgba(0,0,0,.08), 0 10px 7.5px rgba(0,0,0,.12)`.
- Info (padding 8px 12px, border bawah `rgba(0,0,0,0.1)`): nama Barlow Condensed Bold 18px UPPERCASE `ink`; email Barlow 12px `#737373`; **Admin:** badge "ADMIN" (pill `ink`, padding 1px 10px, Barlow 11px putih UPPERCASE tracking 0.55px).
- Item (padding 8px 12px, `rounded-[8px]`, Barlow 14px `ink`, hover latar `black/5`):
  - Customer: Profil saya · Pesanan saya · Wishlist saya
  - Admin: Profil saya · Dashboard admin
- Pemisah border atas, lalu **Keluar** (warna `#b91c1c`) = form POST `/logout` + CSRF.
- Tutup saat klik di luar / Esc (pakai `menu.js` yang ada).

## 4. Menu Brand — dropdown (`8:893`)
- Padding 16px, `rounded-[16px]`, kaca/blur & bayangan sama dengan Menu Akun.
- Judul "PILIH BRAND" (Barlow Condensed Bold 12px, tracking 0.6px, `#737373`), border bawah, jarak 8px.
- Daftar brand dari DB, **kolom lebar 160px, maksimal 8 brand per kolom, kolom bertambah ke samping, tanpa scroll**. Item padding 8px 12px, `rounded-[8px]`, Barlow 14px `ink`, hover `black/5`. Link ke katalog dengan `?brand=<slug>`.
- Bawah: border atas, "LIHAT SEMUA PRODUK →" (Barlow Condensed Bold 12px, tracking 0.6px, `ink`).

## 5. Kartu Produk (`4:109`)
- Padding 4px, `rounded-[12px]`; **hover: latar `#f5f5f5`, nama jadi abu**.
- Gambar: rasio 1:1, latar `#f5f5f5`, border `#e5e5e5`, `rounded-[8px]`; teks "Belum ada gambar" Barlow 14px `#a3a3a3` bila kosong.
- Tombol wishlist (opsional): lingkaran 36px putih, border `#e5e5e5`, kanan 9px / atas 9px, ikon hati 18px (garis; penuh bila sudah disukai). *(lihat Catatan A)*
- Info (padding 8px, gap 2px): harga Barlow Bold 16px hitam; nama Barlow 16px hitam; brand Barlow 14px `#737373`; "Stok habis" Barlow 14px `#b91c1c` bila `total_stock == 0`.

## 6. Tombol
| Komponen | Spesifikasi |
|---|---|
| **Tombol Utama** (`4:146`, form Masuk/Daftar) | lebar penuh, tinggi 52px, pill `ink`, Barlow Condensed Bold 18px putih UPPERCASE tracking 0.9px. Hover `neutral-800`, ditekan `neutral-600`. |
| **Tombol Pill Besar** (`8:1024`) | pill `ink`, padding 12px 28px, gap 16px, Barlow Condensed Bold 16px putih tracking 0.8px + ikon panah 32×12. Hover `ink-muda`, ditekan `neutral-700`. |
| **Tombol Pill Kecil** (`8:1028`) | padding 6px 16px, Barlow Condensed Bold 14px tracking 0.7px (+ panah opsional). |
| **Tombol Pill Garis** (`10:1086`) | sama dengan pill kecil, latar putih, border `ink`. |
| **Tombol Admin** (`4:174`) | pill, border 1.5px, padding 10px 18px, Barlow Condensed Bold 15px UPPERCASE tracking 0.9px. Utama: `#111` teks putih · Bahaya: `#b91c1c` teks putih · Garis: putih, border & teks `#111`. |

## 7. Chip Brand (`4:179`)
- Pill, border 1px, padding 6px 16px, Barlow Condensed Bold 14px UPPERCASE tracking 0.7px.
- Aktif: latar & border `ink`, teks putih. Normal: latar putih, border `#d4d4d4`, teks `ink`, hover `#f5f5f5`.

## 8. Kolom Isian
**Halaman Masuk/Daftar — dengan ikon (`27:2368`)**
- Label Barlow SemiBold 14px `ink`, jarak 6px.
- Kotak: padding 13px 14px, gap 10px, `rounded-[12px]`, latar `#fafafa`, border `#e5e5e5`; ikon kiri 20px (email / gembok / user); input Barlow 16px, placeholder `#a3a3a3`; password punya tombol mata 20px di kanan.
- **Fokus:** border `ink` + latar putih. **Error:** latar `#fef2f2`, border `#dc2626`, di bawahnya ikon error 16px + pesan Barlow 13px `#dc2626`.

**Halaman admin (`4:167`)**
- Label Barlow SemiBold 14px `#111`; kotak putih, border `#a3a3a3`, `rounded-[12px]`, padding 12px 16px, Barlow 16px hitam. Textarea tinggi 120px. Select: ikon chevron 16px di kanan.

## 9. Pesan Flash (`4:152`)
- Padding 12px, `rounded-[8px]`, border kiri 4px, Barlow 16px.
- Sukses: latar `#f0fdf4`, border `#16a34a`, teks `#166534`. Error: latar `#fef2f2`, border `#dc2626`, teks `#991b1b`.

## 10. Label Status (`10:1078`) — dipakai pesanan, pembayaran, user
Pill, padding 3px 10px, Barlow Condensed Bold 12px UPPERCASE tracking 0.6px.
| Nilai DB | Teks | Gaya |
|---|---|---|
| `pending_payment` | Menunggu pembayaran | putih, border `ink`, teks `ink` |
| `awaiting_verification` | Menunggu verifikasi | latar `#e5e5e5`, teks `ink` |
| `paid` / payment `verified` / user aktif | Dibayar / Terverifikasi / Aktif | latar `ink`, teks putih |
| `shipped` | Dikirim | latar `#353b46`, teks putih |
| `completed` / user nonaktif | Selesai / Nonaktif | latar `#f5f5f5`, border `#d4d4d4`, teks `#525252` |
| `cancelled` / payment `rejected` / user terkunci | Dibatalkan / Ditolak / Terkunci | latar `#fef2f2`, border `#fecaca`, teks `#b91c1c` |
Buat sebagai macro Jinja `status_badge(value)` dengan peta nilai → teks & kelas.

## 11. Footer (`8:970`)
**Lengkap** (halaman toko): latar `#fafafa`, border atas `#e5e5e5`; isi 1280px, padding 48px 16px, 4 kolom lebar 282px gap 40px. Judul kolom Barlow Condensed Bold 14px UPPERCASE tracking 0.7px `ink`; isi Barlow 14px `#525252`, gap 8px.
- **Lokasi:** kotak peta 282×282 `rounded-[12px]` border `#e5e5e5` (Google Maps embed `Politeknik Negeri Batam`, `loading="lazy"`, `referrerpolicy="no-referrer"`); di bawahnya "Tower A Politeknik Negeri Batam" + link bergaris bawah "Buka di Google Maps ↗" (`target=_blank rel="noopener noreferrer"`).
- **Informasi:** Semua produk · Kebijakan · Pengembalian · Buat akun (*hanya untuk tamu*).
- **Kontak Admin:** WhatsApp toko (link `wa.me/{{ config.WA_TOKO }}` bila diisi) · admin@pururuna.id · Senin–Sabtu, 09.00–21.00.
- **Media Sosial:** Instagram · TikTok (link `#` dulu).
- Baris copyright: border atas, padding 16px, Barlow 12px `#737373`: "© 2026 Pururuna · Proyek PBL Tim 16".

**Admin** (halaman `/admin`): latar putih, border atas, padding 24px, hanya copyright.

## 12. Header Admin (`33:2209`) — pengganti header toko di `/admin`
- Latar putih, border bawah `#e5e5e5`, isi 1280px padding 16px, `justify-between`. **Tanpa bar pengumuman & kolom cari.**
- Kiri: "PURURUNA" Barlow Condensed ExtraBold 30px tracking 0.3px `#111` + badge "ADMIN" (latar `#111`, `rounded-[4px]`, padding 3px 10px, Barlow Condensed Bold 13px putih tracking 1.56px).
- Kanan (gap 16px): tombol garis "LIHAT TOKO ↗" (pill, border 1.5px `#111`, padding 9px 16px, Barlow Condensed Bold 15px tracking 0.75px) → beranda; avatar lingkaran 32px; "Admin ▾" Barlow SemiBold 15px → Menu Akun (versi Admin).

## 13. Tombol WhatsApp melayang (`8:1033`)
- Lingkaran 56px, latar `#16a34a`, ikon WA putih 28px, bayangan `0 10px 7.5px rgba(0,0,0,.15)`, `fixed` kanan 20px bawah 20px.
- **Hanya di beranda.** Tampil hanya bila `config.WA_TOKO` diisi.

## 14. Lainnya (untuk fitur berikutnya, belum dipakai)
`Jumlah (stepper)` 10:1079 · `Kotak Unggah` 10:1088 · `Foto (kosong)` 10:1055 · `Stat Card` 3:3 · `Menu Card` 3:12 — dikerjakan bersama fiturnya.

## Ikon
Ambil SVG dari Figma (URL sementara, berlaku 7 hari) dan simpan di `static/icons/`, atau pakai ikon garis setara (stroke 1.5–1.8, `currentColor`):
search, wishlist (hati garis & penuh), keranjang (tas), user, email, gembok, mata, error (lingkaran !), chevron bawah, panah kanan 32×12, whatsapp, pin peta.

## Catatan
- **A. Wishlist** ada di desain (ikon header, tombol di kartu, "Wishlist saya") tetapi **belum ada di `fitur.md` maupun ERD**. Keputusan: lihat issue.
- Keranjang: badge jumlah baru berfungsi setelah fitur keranjang; untuk sekarang ikon tampil tanpa badge.
- Teks UI bahasa Indonesia; aksi pengubah data tetap POST + CSRF.
