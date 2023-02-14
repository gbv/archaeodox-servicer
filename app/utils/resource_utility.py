from dpath import util as dp


def process(resource):
    resource = remove_empty_fields(resource)
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
