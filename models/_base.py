from datetime import datetime, timezone


def now_utc():
    return datetime.now(timezone.utc)


def sql_in(column, values):
    """Buat teks CHECK "kolom IN ('a', 'b')" dari tuple whitelist yang sama dengan di Python."""
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"