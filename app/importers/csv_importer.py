import csv, io

from app.utils import resource_utility
from app.field.database import FieldDatabase


def run(file_data, file_name, field_database):
    file_object = io.StringIO(file_data.decode('utf-8'))

    with file_object:
        feature_reader = csv.DictReader(file_object, delimiter=',', quotechar='"')
        items = [resource_utility.process(item) for item in feature_reader]
    
    # TODO Improve
    possible_type = list(filter(lambda t: t.lower() in file_name, FieldDatabase.OBJECT_TYPES))

    if possible_type:
        resource_type = possible_type[0]
        for item in items:
            field_database.populate_resource(item, resource_type)
    else:
        raise ValueError(f'No valid type in {file_name}!')
