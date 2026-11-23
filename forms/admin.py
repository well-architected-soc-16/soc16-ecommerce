import re

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField, TextAreaField, DecimalField,
    SelectField, BooleanField,
)
from wtforms.validators import (
    DataRequired, InputRequired, Length, NumberRange, Optional, ValidationError,
)

from models import AUDIENCES, PRODUCT_TYPES

# Label bahasa Indonesia untuk nilai whitelist (nilai yang disimpan tetap bahasa Inggris)
AUDIENCE_LABELS = {"men": "Pria", "women": "Wanita", "unisex": "Unisex", "kids": "Anak"}
PRODUCT_TYPE_LABELS = {
    "sneakers": "Sneakers", "running": "Lari", "basketball": "Basket",
    "casual": "Kasual", "sandals": "Sandal",
}

UKURAN_MIN, UKURAN_MAX = 30, 50
STOK_MAX = 10_000


def parse_sizes(teks):
    """Ubah teks "40:3, 41:5" jadi {"40": 3, "41": 5}. ValueError kalau formatnya salah."""
    hasil = {}
    for bagian in re.split(r"[,\n]+", teks or ""):
        bagian = bagian.strip()
        if not bagian:
            continue
        cocok = re.fullmatch(r"(\d{2})\s*:\s*(\d{1,5})", bagian)
        if not cocok:
            raise ValueError(f"Format salah: '{bagian}'. Contoh yang benar: 40:3")
        ukuran, stok = cocok.group(1), int(cocok.group(2))
        if not UKURAN_MIN <= int(ukuran) <= UKURAN_MAX:
            raise ValueError(f"Ukuran {ukuran} di luar rentang {UKURAN_MIN}–{UKURAN_MAX}")
        if stok > STOK_MAX:
            raise ValueError(f"Stok ukuran {ukuran} maksimal {STOK_MAX}")
        if ukuran in hasil:
            raise ValueError(f"Ukuran {ukuran} ditulis dua kali")
        hasil[ukuran] = stok
    if not hasil:
        raise ValueError("Isi minimal satu ukuran, contoh: 40:3, 41:5")
    return hasil


class BrandForm(FlaskForm):
    name = StringField("Nama Brand", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Simpan")


class ProductForm(FlaskForm):
    name = StringField("Nama Produk", validators=[DataRequired(), Length(max=200)])
    brand_id = SelectField("Brand", coerce=int, validators=[InputRequired()])
    group_name = StringField(
        "Nama model (untuk varian warna)",
        validators=[Optional(), Length(max=150)],
        description="Produk dari brand yang sama dengan nama model yang sama tampil sebagai pilihan warna. Kosongkan jika tidak ada varian.",
    )
    color = StringField("Warna", validators=[Optional(), Length(max=30)])
    audience = SelectField(
        "Untuk", choices=[(a, AUDIENCE_LABELS[a]) for a in AUDIENCES], validators=[InputRequired()]
    )
    product_type = SelectField(
        "Jenis", choices=[(t, PRODUCT_TYPE_LABELS[t]) for t in PRODUCT_TYPES], validators=[InputRequired()]
    )
    description = TextAreaField("Deskripsi", validators=[Optional(), Length(max=5000)])
    price = DecimalField(
        "Harga (Rp)",
        places=2,
        validators=[InputRequired(message="Harga wajib diisi"), NumberRange(min=0, max=9_999_999_999)],
    )
    sizes = TextAreaField(
        "Ukuran & stok",
        validators=[DataRequired(message="Isi minimal satu ukuran"), Length(max=500)],
        description="Format ukuran:stok, pisahkan dengan koma. Contoh: 40:3, 41:5, 42:0",
    )
    is_featured = BooleanField("Tampilkan di Pilihan Kami")
    is_active = BooleanField("Tampilkan di katalog", default=True)
    submit = SubmitField("Simpan")

    def validate_sizes(self, field):
        try:
            self.parsed_sizes = parse_sizes(field.data)
        except ValueError as e:
            raise ValidationError(str(e))


class DeleteProductForm(FlaskForm):
    confirm = StringField(
        "Ketik nama produk untuk konfirmasi",
        validators=[DataRequired(), Length(max=200)],
    )
    submit = SubmitField("Hapus permanen")
