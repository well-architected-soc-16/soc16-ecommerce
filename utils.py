import re
import unicodedata
from urllib.parse import urlsplit

from flask import request

from extensions import db


def buat_slug(teks):
    teks = unicodedata.normalize("NFKD", teks).encode("ascii", "ignore").decode()
    teks = re.sub(r"[^a-zA-Z0-9]+", "-", teks).strip("-").lower()
    return teks or "item"


def slug_unik(model, teks, abaikan_id=None):
    dasar = buat_slug(teks)[:100]
    slug = dasar
    nomor = 2
    while True:
        pemilik = db.session.execute(
            db.select(model.id).filter_by(slug=slug)
        ).scalar_one_or_none()
        if pemilik is None or pemilik == abaikan_id:
            return slug
        slug = f"{dasar}-{nomor}"
        nomor += 1


def safe_next(target):
    """Kembalikan target hanya kalau berupa path lokal ("/produk/x?a=1"); selain itu None.

    Mencegah open redirect: menolak URL absolut ("https://evil.com"), protocol-relative
    ("//evil.com"), backslash ("/\\evil.com" dibaca browser sebagai "//evil.com"), dan karakter kontrol.
    """
    if not target or not isinstance(target, str) or len(target) > 500:
        return None
    if not target.startswith("/") or target.startswith("//") or "\\" in target:
        return None
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in target):
        return None
    parts = urlsplit(target)
    if parts.scheme or parts.netloc:
        return None
    return target


def current_path():
    """Path + query halaman sekarang, untuk parameter next (mis. "/produk?brand=nike")."""
    query = request.query_string.decode("utf-8", "ignore")
    return request.path + (f"?{query}" if query else "")


def url_with(**changes):
    """URL halaman sekarang dengan parameter query diubah; nilai None menghapus parameter.

    Dipakai tautan urut/filter supaya parameter lain tetap terbawa. Nilai tetap divalidasi
    whitelist di route masing-masing.
    """
    from flask import url_for
    args = request.args.to_dict()
    for key, value in changes.items():
        if value is None:
            args.pop(key, None)
        else:
            args[key] = value
    return url_for(request.endpoint, **(request.view_args or {}), **args)
