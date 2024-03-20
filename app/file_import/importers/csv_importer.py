import csv, io
from dpath import util as dp

from app import settings, messages


def run(file_data, file_name, field_database):
    category = __get_category(file_name)
    file_object = io.StringIO(file_data.decode('utf-8-sig'))

    with file_object:
        csv_reader = csv.DictReader(file_object, delimiter=',', quotechar='"')
        resources = [__get_resource(row, category, field_database) for row in csv_reader]

    for resource in resources:
        existing_identifier = __get_document(resource['identifier'], field_database)['resource']['identifier']
        field_database.populate_resource(resource, existing_identifier)

def __get_category(file_name):
    extracted_category = __extract_category_from_file_name(file_name)
    for category in settings.CSVImporter.ALLOWED_CATEGORIES:
        if extracted_category.replace('+', ':').lower() == category.lower():
            return category
    raise ValueError(f'{messages.FileImport.ERROR_CSV_CATEGORY_NOT_CONFIGURED} {extracted_category}')

def __extract_category_from_file_name(file_name):
    segments = file_name.split('.')
    if len(segments) < 3:
        raise ValueError(messages.FileImport.ERROR_CSV_CATEGORY_NOT_FOUND)
    else:
        return segments[-2]

def __get_resource(row, category, field_database):
    resource = __get_filled_in_fields(row)
    resource['category'] = category
    resource['identifier'] = __get_prefixed_identifier(resource['identifier'], category)
    __inflate(resource)
    __split_relation_targets(resource, field_database)
    return resource

def __get_filled_in_fields(row):
    resource = {}
    for key, value in row.items():
        if str(value).strip():
            resource[key] = value
    return resource

def __inflate(resource):
    nested_keys = list(filter(lambda k: '.' in k, resource.keys()))
    for key in nested_keys:
        dp.new(resource, key, resource[key], separator='.')
        resource.pop(key)

def __split_relation_targets(resource, field_database):
    relations = resource.get('relations', {})
    for relation_name, targets in relations.items():
        target_identifiers = targets.split(';')
        target_ids = [
            __get_document(target_identifier, field_database)['_id'] for target_identifier in target_identifiers
        ]
        resource['relations'][relation_name] = target_ids

def __get_prefixed_identifier(identifier, category):
    prefix = settings.FileImport.CATEGORY_PREFIXES.get(category)
    if prefix is None or identifier.startswith(prefix):
        return identifier
    else:
        return prefix + str(identifier)

def __get_document(identifier, field_database):
    for category in settings.FileImport.CATEGORY_PREFIXES.keys():
        prefixed_identifier = __get_prefixed_identifier(identifier, category)
        document = __perform_search(prefixed_identifier, field_database)
        if document is not None:
            return document
    return field_database.get_or_create_document(identifier)

def __perform_search(identifier, field_database):
    documents = field_database.search({ 'selector': { 'resource.identifier': identifier } })
    if documents and len(documents) > 0:
        return documents[0]
    else:
        return None
