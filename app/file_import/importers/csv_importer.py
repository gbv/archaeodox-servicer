import csv, io
from dpath import util as dp

from app import settings, messages


def run(file_data, file_name, field_database):
    category = __get_category(file_name)
    file_object = io.StringIO(file_data.decode('utf-8-sig'))

    with file_object:
        csv_reader = csv.DictReader(file_object, delimiter=';', quotechar='"')
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
    if 'identifier' not in resource:
        raise ValueError(messages.FileImport.ERROR_CSV_IDENTIFIER_NOT_FOUND)
    resource['category'] = category
    resource['identifier'] = __get_prefixed_identifier(resource['identifier'], category)
    __inflate(resource)
    __split_array_fields(resource)
    __split_relation_targets(resource, field_database)
    __convert_values(resource)
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

def __split_array_fields(resource):
    for field_name, field_content in resource.items():
        if field_name in settings.CSVImporter.ARRAY_FIELDS:
            entries = field_content.split(';')
            resource[field_name] = entries

def __split_relation_targets(resource, field_database):
    relations = resource.get('relations', {})
    for relation_name, targets in relations.items():
        target_identifiers = targets.split(';')
        target_ids = [
            __get_document(target_identifier, field_database)['_id'] for target_identifier in target_identifiers
        ]
        resource['relations'][relation_name] = target_ids

def __convert_values(resource):
    for field_name, field_content in resource.items():
        if field_content == 'true':
            resource[field_name] = True
        elif field_content == 'false':
            resource[field_name] = False
        elif field_name in settings.CSVImporter.INT_FIELDS:
            resource[field_name] = int(field_content)
        elif field_name in settings.CSVImporter.FLOAT_FIELDS:
            resource[field_name] = float(field_content)
        elif field_name in settings.CSVImporter.DATING_FIELDS:
            __convertDatings(field_content)
        elif field_name in settings.CSVImporter.DIMENSION_FIELDS:
            __convertDimensions(field_content)

def __convertDatings(datings):
    for dating in datings:
        if 'begin' in dating and 'inputYear' in dating['begin']:
            dating['begin']['inputYear'] = int(dating['begin']['inputYear'])
        if 'end' in dating and 'inputYear' in dating['end']:
            dating['end']['inputYear'] = int(dating['end']['inputYear'])
        if 'isImprecise' in dating:
            dating['isImprecise'] = dating['isImprecise'] == True
        if 'isUncertain' in dating: 
            dating['isUncertain'] = dating['isUncertain'] == True

def __convertDimensions(dimensions):
    for dimension in dimensions:
        if 'inputValue' in dimension:
            dimension['inputValue'] = int(dimension['inputValue'])
        if 'inputRangeEndValue' in dimension:
            dimension['inputRangeEndValue'] = int(dimension['inputRangeEndValue'])
        if 'isImprecise' in dimension:
            dimension['isImprecise'] = dimension['isImprecise'] == True

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
