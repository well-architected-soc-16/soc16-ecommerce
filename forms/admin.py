import re
from decimal import Decimal, InvalidOperation

from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField, TextAreaField, DecimalField,
    SelectField, SelectMultipleField, BooleanField,
)
from wtforms.validators import (
    DataRequired, InputRequired, Length, NumberRange, Optional, Regexp, StopValidation, ValidationError,
)
from wtforms.widgets import CheckboxInput, ListWidget, TextInput

from models import AUDIENCES, PRODUCT_TYPES, COLORS, MAX_COLORS, SIZE_MIN, SIZE_MAX

# Label bahasa Indonesia untuk nilai whitelist (nilai yang disimpan tetap bahasa Inggris)
AUDIENCE_LABELS = {"men": "Pria", "women": "Wanita", "unisex": "Unisex", "kids": "Anak"}
PRODUCT_TYPE_LABELS = {
    "sneakers": "Sneakers", "running": "Lari", "basketball": "Basket",
    "casual": "Kasual", "sandals": "Sandal",
}

STOK_MAX = 10_000


def parse_sizes(teks):
    """Ubah teks "40:3, 40.5:2" jadi {"40": 3, "40.5": 2}. ValueError kalau formatnya salah.

    Ukuran EU bulat atau .5, rentang SIZE_MIN–SIZE_MAX (50.5 tidak). Sama dengan CHECK
    ck_product_sizes_size di database.
    """
    hasil = {}
    for bagian in re.split(r"[,\n]+", teks or ""):
        bagian = bagian.strip()
        if not bagian:
            continue
        cocok = re.fullmatch(r"(\d{2})(?:\.(\d))?\s*:\s*(\d{1,5})", bagian)
        if not cocok:
            raise ValueError(f"Format salah: '{bagian}'. Contoh yang benar: 40:3 atau 40.5:2")
        bulat, desimal, stok = cocok.group(1), cocok.group(2), int(cocok.group(3))
        if desimal not in (None, "5"):
            raise ValueError(f"Ukuran {bulat}.{desimal} tidak valid: pakai bilangan bulat atau .5 (mis. 40.5)")
        ukuran = bulat if desimal is None else f"{bulat}.5"
        if not SIZE_MIN <= float(ukuran) <= SIZE_MAX:
            raise ValueError(f"Ukuran {ukuran} di luar rentang {SIZE_MIN}–{SIZE_MAX}")
        if stok > STOK_MAX:
            raise ValueError(f"Stok ukuran {ukuran} maksimal {STOK_MAX}")
        if ukuran in hasil:
            raise ValueError(f"Ukuran {ukuran} ditulis dua kali")
        hasil[ukuran] = stok
    if not hasil:
        raise ValueError("Isi minimal satu ukuran, contoh: 40:3, 40.5:2")
    return hasil


class ChoiceField(SelectField):
    """SelectField dengan pesan whitelist bahasa Indonesia (bawaan WTForms: "Not a valid choice.")."""

    def pre_validate(self, form):
        try:
            super().pre_validate(form)
        except ValidationError:
            raise ValidationError("Pilihan tidak valid.")


class MultiCheckboxField(SelectMultipleField):
    """Pilihan ganda berupa checkbox; nilai di luar choices ditolak dengan pesan Indonesia."""
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()

    def pre_validate(self, form):
        try:
            super().pre_validate(form)
        except ValidationError:
            raise ValidationError("Pilihan tidak valid.")


class PriceField(DecimalField):
    """Harga sebagai isian teks (bukan type=number, yang ditampilkan browser ber-locale Indonesia
    dengan koma, mis. "1700000,00"). Tampil "1700000" atau "1700000.50"; koma desimal tetap diterima.
    """
    widget = TextInput()
    PATTERN = re.compile(r"\d{1,10}(?:[.,]\d{1,2})?")

    def _value(self):
        if self.raw_data:
            return self.raw_data[0].strip().replace(",", ".")
        if self.data is None:
            return ""
        value = self.data.quantize(Decimal("0.01"))
        return str(value.to_integral()) if value == value.to_integral() else str(value)

    def pre_validate(self, form):
        # Format sudah salah: cukup satu pesan, jangan lanjut ke NumberRange
        if self.process_errors:
            raise StopValidation()

    def process_formdata(self, valuelist):
        if not valuelist:
            return
        raw = (valuelist[0] or "").strip()
        if not raw:
            self.data = None
            return
        if not self.PATTERN.fullmatch(raw):
            self.data = None
            raise ValueError("Harga harus angka tanpa titik ribuan, mis. 1700000 atau 1700000.50")
        try:
            self.data = Decimal(raw.replace(",", "."))
        except InvalidOperation as exc:
            self.data = None
            raise ValueError("Harga harus angka, mis. 1700000") from exc


def strip_or_none(value):
    """Isian teks opsional: spasi tepi dibuang, kosong -> None (supaya UNIQUE sku tidak bentrok di "")."""
    if isinstance(value, str):
        value = value.strip()
    return value or None


class BrandForm(FlaskForm):
    name = StringField("Nama Brand", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Simpan")


class ProductForm(FlaskForm):
    name = StringField("Nama Produk", validators=[DataRequired(), Length(max=200)])
    brand_id = ChoiceField("Brand", coerce=int, validators=[InputRequired()])
    group_name = StringField(
        "Nama model (untuk varian warna)",
        validators=[Optional(), Length(max=150)],
        description="Produk dari brand yang sama dengan nama model yang sama tampil sebagai pilihan warna. Kosongkan jika tidak ada varian.",
    )
    # Whitelist warna: nilai di luar COLORS ditolak pre_validate. Nama field = property
    # Product.color_keys supaya ProductForm(obj=product) langsung terisi saat edit.
    color_keys = MultiCheckboxField(
        "Warna",
        choices=[(key, label) for key, (label, _hex) in COLORS.items()],
        description=f"Pilih 1–{MAX_COLORS} warna. Urutan mengikuti daftar.",
    )
    audience = ChoiceField(
        "Untuk", choices=[(a, AUDIENCE_LABELS[a]) for a in AUDIENCES], validators=[InputRequired()]
    )
    product_type = ChoiceField(
        "Jenis", choices=[(t, PRODUCT_TYPE_LABELS[t]) for t in PRODUCT_TYPES], validators=[InputRequired()]
    )
    material = StringField(
        "Bahan", filters=[strip_or_none], validators=[Optional(), Length(max=100)],
        description="Contoh: Kulit, Suede, Mesh",
    )
    fit = StringField(
        "Fit", filters=[strip_or_none], validators=[Optional(), Length(max=50)],
        description="Contoh: Regular, Lebar, Sempit",
    )
    sku = StringField(
        "Kode (SKU)",
        filters=[strip_or_none, lambda v: v.upper() if v else v],
        validators=[
            Optional(), Length(max=50),
            Regexp(r"^[A-Z0-9][A-Z0-9._-]*$", message="Kode hanya huruf, angka, titik, minus, atau garis bawah."),
        ],
        description="Kode produk versi toko, mis. ADS-SAMBA-WHT. Boleh kosong.",
    )
    description = TextAreaField("Deskripsi", validators=[Optional(), Length(max=5000)])
    price = PriceField(
        "Harga (Rp)",
        places=2,
        render_kw={"inputmode": "decimal", "autocomplete": "off"},
        validators=[
            InputRequired(message="Harga wajib diisi"),
            NumberRange(min=0, max=9_999_999_999, message="Harga harus antara 0 dan 9.999.999.999"),
        ],
    )
    sizes = TextAreaField(
        "Ukuran & stok",
        validators=[DataRequired(message="Isi minimal satu ukuran"), Length(max=500)],
        description=f"Format ukuran:stok, pisahkan dengan koma. Ukuran EU bulat atau .5 ({SIZE_MIN}–{SIZE_MAX}). Contoh: 40:3, 40.5:2, 41:0",
    )
    is_limited = BooleanField("Edisi terbatas")
    is_featured = BooleanField("Tampilkan di Pilihan Kami")
    is_active = BooleanField("Tampilkan di katalog", default=True)
    submit = SubmitField("Simpan")

    def validate_color_keys(self, field):
        field.data = list(dict.fromkeys(field.data or []))  # buang duplikat, urutan tetap
        if not field.data:
            raise ValidationError("Pilih minimal satu warna.")
        if len(field.data) > MAX_COLORS:
            raise ValidationError(f"Maksimal {MAX_COLORS} warna.")

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
