import click
from extensions import db
from models import User


@click.command("buat-admin")
@click.option("--email", prompt=True)
@click.option("--nama", prompt=True)
@click.password_option()
def buat_admin(email, nama, password):
    email = email.strip().lower()

    sudah_ada = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()
    if sudah_ada:
        raise click.ClickException("Email sudah terdaftar.")

    if len(password) < 12:
        raise click.ClickException("Password admin minimal 12 karakter.")

    admin = User(email=email, nama=nama.strip(), role="admin")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f"Admin {email} berhasil dibuat.")