import csv, io
from dpath import util as dp

from app import settings


def run(file_data, file_name, field_database):
    category = __get_category(file_name)
    file_object = io.StringIO(file_data.decode('utf-8'))

    with file_object:
        csv_reader = csv.DictReader(file_object, delimiter=',', quotechar='"')
        resources = [__get_resource(row, field_database) for row in csv_reader]

    for resource in resources:
        resource['category'] = category
        field_database.populate_resource(resource)

def __get_category(file_name):
    extracted_category = __extract_category_from_file_name(file_name)
    for category in settings.CSVImporter.ALLOWED_CATEGORIES:
        if extracted_category.replace('+', ':').lower() == category.lower():
            return category
    raise ValueError(f'Failed to import file: {file_name}. Category {extracted_category} is not a valid category.')

def __extract_category_from_file_name(file_name):
    segments = file_name.split('.')
    if len(segments) < 3:
        raise ValueError(f'No category found in file name: {file_name}')
    else:
        return segments[-2]

def __get_resource(row, field_database):
    resource = __get_filled_in_fields(row)
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
        target_ids = [field_database.get_or_create_document(target_identifier)['_id'] for target_identifier in target_identifiers]
        resource['relations'][relation_name] = target_ids
