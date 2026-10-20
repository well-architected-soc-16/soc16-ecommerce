import re
import unicodedata

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