import re, datetime

from app import settings, messages
from app.dante.database import DanteDatabase


def run(cloned_asset, document_type_concept_id, user_name, file_name, pool, fylr):
    person = __get_person(user_name, fylr)
    document_type_concept = __get_document_type_concept(document_type_concept_id)
    (description, date) = __parse_file_name(file_name)
    __create_fylr_object(cloned_asset, document_type_concept, person, description, date, pool, fylr)

def __get_person(user_name, fylr):
    result = fylr.get_object_by_field_value('person_institution', 'vollstaendiger_name', user_name)
    if result is None:
        raise ValueError(f'{messages.FileImport.ERROR_PERSON_NOT_FOUND} {user_name}')
    return result

def __get_document_type_concept(concept_id):
    return {
        'conceptURI': f'{settings.Dante.VOCABULARY_URI_BASE}/{settings.FileImport.DOCUMENT_TYPE_VOCABULARY_NAME}/{concept_id}',
        'conceptName': __get_concept_name(concept_id)
    }

def __parse_file_name(file_name):
    file_name = __remove_extension(file_name)
    second_underscore_index = file_name.find('_', file_name.find('_') + 1)
    description = file_name[second_underscore_index:].replace('_', ' ').strip()
    date = None
    if re.match(r'^ \d{6}$', description[-7:]):
        date = __parse_date(description[-6:])
        description = description[:-6].strip()
    return (description, date)

def __remove_extension(file_name):
    extension_index = file_name.find('.')
    return file_name[:extension_index]

def __parse_date(date_string):
    year = '20' + date_string[:2]
    month = date_string[2:-2]
    day = date_string[-2:]
    __validate_date(date_string, year, month, day)
    return f'{year}-{month}-{day}'

def __validate_date(date_string, year, month, day):
    try:
        datetime.datetime(int(year), int(month), int(day))
    except Exception:
        raise ValueError(f'{messages.FileImport.ERROR_INVALID_DATE} {date_string}')

def __get_concept_name(concept_id):
    dante_database = DanteDatabase(settings.Dante.HOST_URL)
    concept = dante_database.get(settings.FileImport.DOCUMENT_TYPE_VOCABULARY_NAME, concept_id)
    if concept is None:
        raise ValueError(f'{messages.FileImport.ERROR_DOCUMENT_TYPE_CONCEPT_NOT_FOUND} {concept_id}')
    return concept['prefLabel']['de']

def __create_fylr_object(cloned_asset, document_type_concept, person, description, date, pool, fylr):
    object = {
        'typ': document_type_concept,
        'datei': cloned_asset,
        'lk_bearbeiter': person,
        'beschreibung': description
    }

    if date is not None:
        object['datum'] = {
            'value': date
        }

    fylr.create_object('dokumente_manuell', object, pool=pool)
