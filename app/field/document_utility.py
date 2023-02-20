from datetime import datetime, timezone


def get_document(id, resource):
    return {
        '_id': id,
        'resource': resource,
        'created': {
            'user': 'easydb',
            'date': __get_date()
        },
        'modified': []
    }

def __get_date():
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
