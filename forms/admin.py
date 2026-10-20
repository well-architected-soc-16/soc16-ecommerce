from flask_wtf import FlaskForm
from wtforms import (
    StringField, SubmitField, TextAreaField, DecimalField,
    IntegerField, SelectField, BooleanField,
)
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, Optional


class CategoryForm(FlaskForm):
    nama = StringField("Nama Kategori", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Simpan")


class ProductForm(FlaskForm):
    nama = StringField("Nama Produk", validators=[DataRequired(), Length(max=200)])
    category_id = SelectField("Kategori", coerce=int, validators=[InputRequired()])
    deskripsi = TextAreaField("Deskripsi", validators=[Optional(), Length(max=5000)])
    harga = DecimalField(
        "Harga (Rp)",
        places=2,
        validators=[InputRequired(message="Harga wajib diisi"), NumberRange(min=0, max=9_999_999_999)],
    )
    stock = IntegerField(
        "Stok",
        validators=[InputRequired(message="Stok wajib diisi"), NumberRange(min=0, max=1_000_000)],
    )
    is_active = BooleanField("Tampilkan di katalog", default=True)
    submit = SubmitField("Simpan")