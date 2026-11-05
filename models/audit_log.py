from datetime import datetime, timezone
from extensions import db


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    event = db.Column(db.String(50), nullable=False, index=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    email = db.Column(db.String(255), nullable=True)
    src_ip = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    detail = db.Column(db.JSON, nullable=False, default=dict)

    user = db.relationship("User")
