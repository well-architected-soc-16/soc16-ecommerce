import click
from flask.cli import with_appcontext

from extensions import db
from models import User, Brand, ProductGroup, Product, ProductColor, ProductSize
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


# Data contoh untuk development: brand, model (grup varian), produk + warna + stok per ukuran
SEED_BRANDS = ["Adidas", "Nike", "New Balance", "Puma", "Converse"]


def _p(brand, group, name, colors, audience, ptype, price, sizes, featured=False, **spec):
    """Satu produk contoh. colors = kunci COLORS (1–3), sizes = {ukuran EU: stok}, spec = material/fit/sku/is_limited."""
    return dict(brand=brand, group=group, name=name, colors=colors, audience=audience, ptype=ptype,
                price=price, sizes=sizes, featured=featured, spec=spec)


SEED_PRODUCTS = [
    _p("Adidas", "Samba OG", "Adidas Samba OG Putih", ["white", "black"], "unisex", "sneakers", 1_700_000,
       {"39": 3, "40": 5, "41": 4, "42": 2}, True, material="Kulit", fit="Regular", sku="ADS-SAMBA-WHT"),
    _p("Adidas", "Samba OG", "Adidas Samba OG Hitam", ["black", "white"], "unisex", "sneakers", 1_700_000,
       {"40": 2, "41": 1, "42": 0}, material="Kulit", fit="Regular", sku="ADS-SAMBA-BLK"),
    _p("Adidas", None, "Adidas Ultraboost Light", ["black"], "men", "running", 2_900_000,
       {"41": 4, "42": 3, "42.5": 2, "43": 2}, material="Primeknit", fit="Regular", sku="ADS-UBL-BLK"),
    _p("Nike", "Air Force 1", "Nike Air Force 1 Putih", ["white"], "unisex", "sneakers", 1_550_000,
       {"38": 6, "39": 6, "40": 5, "41": 4}, True, material="Kulit", fit="Regular", sku="NKE-AF1-WHT"),
    _p("Nike", "Air Force 1", "Nike Air Force 1 Hitam", ["black"], "unisex", "sneakers", 1_550_000,
       {"40": 2, "41": 1}, sku="NKE-AF1-BLK"),
    _p("Nike", None, "Nike Pegasus 41", ["blue", "orange"], "men", "running", 2_100_000,
       {"41": 3, "42": 3, "43": 1}, material="Mesh", fit="Regular", sku="NKE-PEG41-BLU"),
    _p("Nike", None, "Nike Giannis Immortality 4", ["red"], "men", "basketball", 1_400_000,
       {"42": 2, "43": 2, "44": 1}, sku="NKE-GIA4-RED"),
    _p("New Balance", "530", "New Balance 530 Silver", ["silver", "white", "navy"], "unisex", "sneakers", 1_600_000,
       {"38": 3, "39": 4, "40": 4}, True, material="Mesh & sintetis", fit="Regular", sku="NB-530-SLV"),
    _p("New Balance", "530", "New Balance 530 Putih", ["white"], "women", "sneakers", 1_600_000,
       {"37": 2, "38": 2}, sku="NB-530-WHT"),
    _p("Puma", None, "Puma Palermo", ["green", "cream"], "unisex", "casual", 1_300_000,
       {"39": 1, "40": 1}, material="Suede", fit="Sempit", sku="PMA-PAL-GRN", is_limited=True),
    _p("Converse", None, "Converse Chuck 70 Hi", ["black"], "unisex", "casual", 1_100_000,
       {"38": 5, "39": 5, "40": 5, "41": 5}, material="Kanvas", fit="Regular", sku="CNV-C70-BLK"),
    _p("Converse", None, "Converse Chuck Taylor Kids", ["red"], "kids", "casual", 650_000,
       {"28": 2, "28.5": 2, "29": 3, "29.5": 1}, material="Kanvas", fit="Regular", sku="CNV-CTK-RED"),
]


@click.command("seed")
@with_appcontext
def seed():
    """Isi data contoh. Hanya jalan kalau tabel produk masih kosong."""
    if db.session.scalar(db.select(db.func.count(Product.id))):
        raise click.ClickException("Tabel produk sudah berisi data. Seed dibatalkan.")

    brands = {name: Brand(name=name, slug=buat_slug(name)) for name in SEED_BRANDS}
    groups = {}  # kunci (brand, model): grup varian berlaku per brand
    for item in SEED_PRODUCTS:
        key = (item["brand"], item["group"])
        if item["group"] and key not in groups:
            groups[key] = ProductGroup(brand=brands[item["brand"]], name=item["group"])
        product = Product(
            brand=brands[item["brand"]],
            group=groups.get(key),
            name=item["name"],
            slug=buat_slug(item["name"]),
            description=f"{item['name']}. Data contoh untuk pengembangan.",
            audience=item["audience"],
            product_type=item["ptype"],
            price=item["price"],
            is_featured=item["featured"],
            colors=[ProductColor(color=c) for c in item["colors"]],
            sizes=[ProductSize(size=s, stock=n) for s, n in item["sizes"].items()],
            **item["spec"],
        )
        db.session.add(product)

    db.session.commit()
    click.echo(f"Seed selesai: {len(brands)} brand, {len(SEED_PRODUCTS)} produk.")
