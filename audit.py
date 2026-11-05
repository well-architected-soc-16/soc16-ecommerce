import json
import logging
from datetime import datetime, timezone, timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import request, has_request_context

from extensions import db
from models import AuditLog

WIB = timezone(timedelta(hours=7))
logger = logging.getLogger("ecommerce.audit")


def init_audit(app):
    path = Path(app.config["AUDIT_LOG_PATH"])
    path.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(path, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))

    logger.handlers.clear()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False


def catat(event, user=None, email=None, **detail):
    src_ip = None
    user_agent = None
    if has_request_context():
        src_ip = request.remote_addr
        user_agent = (request.user_agent.string or "")[:200]

    if user is not None and email is None:
        email = user.email
    if email is not None:
        email = str(email)[:255]

    try:
        db.session.add(AuditLog(
            event=event,
            user_id=user.id if user else None,
            email=email,
            src_ip=src_ip,
            user_agent=user_agent,
            detail=detail,
        ))
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.error(json.dumps({"event": "audit_db_error", "failed_event": event}))

    baris = {
        **detail,
        "timestamp": datetime.now(WIB).isoformat(timespec="seconds"),
        "app": "ecommerce",
        "event": event,
        "user_id": user.id if user else None,
        "email": email,
        "role": user.role if user else None,
        "src_ip": src_ip,
        "user_agent": user_agent,
    }
    logger.info(json.dumps(baris, ensure_ascii=False, default=str))