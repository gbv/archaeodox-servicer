import csv, io

from app import settings
from app.utils import resource_utility
from app.field.database import FieldDatabase


def run(file_data, file_name, field_database):
    category = __get_category(file_name)
    file_object = io.StringIO(file_data.decode('utf-8'))

    with file_object:
        csv_reader = csv.DictReader(file_object, delimiter=',', quotechar='"')
        resources = [resource_utility.process(resource) for resource in csv_reader]

    for resource in resources:
        resource['category'] = category
        field_database.populate_resource(resource)

def __get_category(file_name):
    extracted_category = __extract_category_from_file_name(file_name)
    for category in settings.CSVImporter.ALLOWED_CATEGORIES:
        if extracted_category.lower() == category.lower():
            return category
    raise ValueError(f'Failed to import file: {file_name}. Category {extracted_category} is not a valid category.')

def __extract_category_from_file_name(file_name):
    segments = file_name.split('.')
    if len(segments) < 3:
        raise ValueError(f'No category found in file name: {file_name}')
    else:
        return segments[-2]
