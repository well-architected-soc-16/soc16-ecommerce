from extensions import db
from models._base import now_utc, sql_in

ORDER_STATUSES = (
    "pending_payment",
    "awaiting_verification",
    "paid",
    "shipped",
    "completed",
    "cancelled",
)
PAYMENT_STATUSES = ("pending", "verified", "rejected")
PAYMENT_METHODS = ("bank_transfer", "ewallet")


class Order(db.Model):
    __tablename__ = "orders"
    __table_args__ = (
        db.CheckConstraint(sql_in("status", ORDER_STATUSES), name="status"),
        db.CheckConstraint("subtotal >= 0", name="subtotal"),
        db.CheckConstraint("shipping_cost >= 0", name="shipping_cost"),
        db.CheckConstraint("total_amount >= 0", name="total_amount"),
        db.Index("ix_orders_user_created", "user_id", "created_at"),
        db.Index("ix_orders_status_created", "status", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    order_number = db.Column(db.String(30), unique=True, nullable=False)  # acak, bukan berurutan
    status = db.Column(db.String(30), nullable=False, default="pending_payment")
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)
    shipping_cost = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    recipient_name = db.Column(db.String(100), nullable=False)
    recipient_phone = db.Column(db.String(20), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    paid_at = db.Column(db.DateTime(timezone=True), nullable=True)
    shipped_at = db.Column(db.DateTime(timezone=True), nullable=True)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)

    user = db.relationship("User")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payment = db.relationship(
        "Payment", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )


class OrderItem(db.Model):
    __tablename__ = "order_items"
    __table_args__ = (
        db.CheckConstraint("quantity > 0", name="quantity"),
        db.CheckConstraint("unit_price >= 0", name="unit_price"),
        db.CheckConstraint("subtotal >= 0", name="subtotal"),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_size_id = db.Column(
        db.Integer, db.ForeignKey("product_sizes.id", ondelete="SET NULL"), nullable=True
    )
    # Snapshot saat checkout: nota tidak berubah walau produk diedit/dihapus
    product_name = db.Column(db.String(200), nullable=False)
    size = db.Column(db.String(10), nullable=False)
    color = db.Column(db.String(30), nullable=True)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False)

    order = db.relationship("Order", back_populates="items")
    product_size = db.relationship("ProductSize")


class Payment(db.Model):
    __tablename__ = "payments"
    __table_args__ = (
        db.CheckConstraint(sql_in("status", PAYMENT_STATUSES), name="status"),
        db.CheckConstraint(sql_in("method", PAYMENT_METHODS), name="method"),
        db.CheckConstraint("amount >= 0", name="amount"),
        db.Index("ix_payments_status_uploaded", "status", "uploaded_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(
        db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    method = db.Column(db.String(20), nullable=False)
    proof_filename = db.Column(db.String(255), nullable=False)  # nama acak, di luar web root
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    rejection_reason = db.Column(db.Text, nullable=True)
    verified_by = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc)
    verified_at = db.Column(db.DateTime(timezone=True), nullable=True)

    order = db.relationship("Order", back_populates="payment")
    verifier = db.relationship("User")