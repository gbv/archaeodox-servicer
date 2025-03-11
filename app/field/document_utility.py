from datetime import datetime, timezone


def get_document(id, resource):
    return {
        '_id': id,
        'resource': resource,
        'created': __get_action(),
        'modified': []
    }

def add_modified_entry(document):
    if 'modified' not in document:
        document['modified'] = []
    document['modified'].append(__get_action())

def __get_action():
    return {
        'user': 'archaeoDox',
        'date': __get_date()
    }

def __get_date():
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
