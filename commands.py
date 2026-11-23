import click
from flask.cli import with_appcontext

from extensions import db
from models import User, Brand, ProductGroup, Product, ProductSize
from utils import buat_slug


@click.command("buat-admin")
@click.option("--email", prompt=True)
@click.option("--name", prompt="Nama")
@click.password_option()
@with_appcontext
def create_admin(email, name, password):
    email = email.strip().lower()

    exists = db.session.execute(db.select(User.id).filter_by(email=email)).first()
    if exists:
        raise click.ClickException("Email sudah terdaftar.")

    if len(password) < 12:
        raise click.ClickException("Password admin minimal 12 karakter.")

    admin = User(email=email, name=name.strip(), role="admin")
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    click.echo(f"Admin {email} berhasil dibuat.")


# Data contoh untuk development: brand, model (grup varian), produk + stok per ukuran
SEED_BRANDS = ["Adidas", "Nike", "New Balance", "Puma", "Converse"]
SEED_PRODUCTS = [
    # (brand, model/grup, nama, warna, untuk, jenis, harga, {ukuran: stok}, unggulan)
    ("Adidas", "Samba OG", "Adidas Samba OG Putih", "Putih", "unisex", "sneakers", 1_700_000, {"39": 3, "40": 5, "41": 4, "42": 2}, True),
    ("Adidas", "Samba OG", "Adidas Samba OG Hitam", "Hitam", "unisex", "sneakers", 1_700_000, {"40": 2, "41": 1, "42": 0}, False),
    ("Adidas", None, "Adidas Ultraboost Light", "Hitam", "men", "running", 2_900_000, {"41": 4, "42": 3, "43": 2}, False),
    ("Nike", "Air Force 1", "Nike Air Force 1 Putih", "Putih", "unisex", "sneakers", 1_550_000, {"38": 6, "39": 6, "40": 5, "41": 4}, True),
    ("Nike", "Air Force 1", "Nike Air Force 1 Hitam", "Hitam", "unisex", "sneakers", 1_550_000, {"40": 2, "41": 1}, False),
    ("Nike", None, "Nike Pegasus 41", "Biru", "men", "running", 2_100_000, {"41": 3, "42": 3, "43": 1}, False),
    ("Nike", None, "Nike Giannis Immortality 4", "Merah", "men", "basketball", 1_400_000, {"42": 2, "43": 2, "44": 1}, False),
    ("New Balance", "530", "New Balance 530 Silver", "Silver", "unisex", "sneakers", 1_600_000, {"38": 3, "39": 4, "40": 4}, True),
    ("New Balance", "530", "New Balance 530 Putih", "Putih", "women", "sneakers", 1_600_000, {"37": 2, "38": 2}, False),
    ("Puma", None, "Puma Palermo", "Hijau", "unisex", "casual", 1_300_000, {"39": 0, "40": 0}, False),
    ("Converse", None, "Converse Chuck 70 Hi", "Hitam", "unisex", "casual", 1_100_000, {"38": 5, "39": 5, "40": 5, "41": 5}, False),
    ("Converse", None, "Converse Chuck Taylor Kids", "Merah", "kids", "casual", 650_000, {"30": 3, "31": 3, "32": 2}, False),
]


@click.command("seed")
@with_appcontext
def seed():
    """Isi data contoh. Hanya jalan kalau tabel produk masih kosong."""
    if db.session.scalar(db.select(db.func.count(Product.id))):
        raise click.ClickException("Tabel produk sudah berisi data. Seed dibatalkan.")

    brands = {name: Brand(name=name, slug=buat_slug(name)) for name in SEED_BRANDS}
    groups = {}  # kunci (brand, model): grup varian berlaku per brand
    for brand, group, name, color, audience, ptype, price, sizes, featured in SEED_PRODUCTS:
        if group and (brand, group) not in groups:
            groups[(brand, group)] = ProductGroup(brand=brands[brand], name=group)
        product = Product(
            brand=brands[brand],
            group=groups.get((brand, group)),
            name=name,
            slug=buat_slug(name),
            description=f"{name}. Data contoh untuk pengembangan.",
            color=color,
            audience=audience,
            product_type=ptype,
            price=price,
            is_featured=featured,
            sizes=[ProductSize(size=s, stock=n) for s, n in sizes.items()],
        )
        db.session.add(product)

    db.session.commit()
    click.echo(f"Seed selesai: {len(brands)} brand, {len(SEED_PRODUCTS)} produk.")
