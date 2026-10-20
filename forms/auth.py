from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Regexp


class RegisterForm(FlaskForm):
    nama = StringField("Nama", validators=[DataRequired(), Length(max=100)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, max=128, message="Password 8–128 karakter"),
            Regexp(r"^(?=.*[A-Za-z])(?=.*\d).+$", message="Password harus berisi huruf dan angka"),
        ],
    )
    konfirmasi = PasswordField(
        "Konfirmasi Password",
        validators=[DataRequired(), EqualTo("password", message="Password tidak sama")],
    )
    submit = SubmitField("Daftar")