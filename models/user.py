from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models._base import now_utc, sql_in

ROLES = ("customer", "admin")


class User(db.Model):
    __tablename__ = "users"
    __table_args__ = (
        db.CheckConstraint(sql_in("role", ROLES), name="role"),
        db.CheckConstraint("failed_login_count >= 0", name="failed_login_count"),
        db.CheckConstraint("email = lower(email)", name="email_lowercase"),
    )

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)  # selalu lowercase
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)  # alamat default untuk checkout
    role = db.Column(db.String(20), nullable=False, default="customer")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    failed_login_count = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, onupdate=now_utc)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_locked(self):
        return self.locked_until is not None and self.locked_until > now_utc()

    @property
    def is_admin(self):
        return self.role == "admin"