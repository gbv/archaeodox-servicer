from datetime import datetime, timezone


def get_date():
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
