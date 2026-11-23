from extensions import db
from models._base import now_utc


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    __table_args__ = (
        # filter per event + rentang waktu, dan retensi 90 hari
        db.Index("ix_audit_logs_event_created", "event", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=now_utc, index=True)
    event = db.Column(db.String(50), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    email = db.Column(db.String(255), nullable=True)
    src_ip = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(200), nullable=True)
    detail = db.Column(db.JSON, nullable=False, default=dict)  # jangan pernah berisi password

    user = db.relationship("User")