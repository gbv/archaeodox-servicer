from dpath import util as dp


def process(resource):
    resource = remove_empty_fields(resource)
    split_relation_targets(resource)
    return inflate(resource)

def inflate(resource):
    nested_keys = list(filter(lambda k: '.' in k, resource.keys()))
    for key in nested_keys:
        dp.new(resource, key, resource[key], separator='.')
        resource.pop(key)
    return resource

def remove_empty_fields(resource):
    sanitized = {}
    for key, value in resource.items():
        if str(value).strip():
            sanitized[key] = value
    return sanitized

def split_relation_targets(resource, field_database):
    relations = resource.get('relations', {})
    for relation_name, targets in relations.items():
        target_identifiers = targets.split(';')
        target_ids = [field_database.get_or_create_document(target_identifier)['_id'] for target_identifier in target_identifiers]
        resource['relations'][relation_name] = target_ids
