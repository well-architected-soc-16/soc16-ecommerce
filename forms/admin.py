from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class CategoryForm(FlaskForm):
    nama = StringField("Nama Kategori", validators=[DataRequired(), Length(max=100)])
    submit = SubmitField("Simpan")