import re, datetime

from app import settings, messages
from app.dante.database import DanteDatabase


def run(cloned_asset, document_type_concept_id, user_name, file_name, vorgang_name, fylr):
    (vorgang, person, document_type_concept, description, date) = __get_document_data(
        document_type_concept_id, user_name, file_name, vorgang_name, fylr
    )
    document = __get_document_object(document_type_concept, description, date, fylr)
    if document is not None:
        __update_document_object(document, cloned_asset, person, fylr)
    else:
        document = __create_document_object(cloned_asset, document_type_concept, person, description, date, vorgang, fylr)
        __add_document_to_vorgang(document, vorgang, fylr)

def __get_document_data(document_type_concept_id, user_name, file_name, vorgang_name, fylr):
    vorgang = __get_vorgang(vorgang_name, fylr)
    person = __get_person(user_name, fylr)
    document_type_concept = __get_document_type_concept(document_type_concept_id)
    (description, date) = __parse_file_name(file_name)
    return (vorgang, person, document_type_concept, description, date)

def __get_vorgang(vorgang_name, fylr):
    vorgang = fylr.get_object_by_field_values('vorgang', { 'vorgang': vorgang_name })
    if vorgang is None:
        raise ValueError(f'{messages.FileImport.ERROR_VORGANG_NOT_FOUND} {vorgang_name}')
    return vorgang

def __get_person(user_name, fylr):
    result = fylr.get_object_by_field_values('person_institution', { 'vollstaendiger_name':  user_name })
    if result is None:
        raise ValueError(f'{messages.FileImport.ERROR_PERSON_NOT_FOUND} {user_name}')
    return result

def __get_document_type_concept(concept_id):
    return {
        'conceptURI': f'{settings.Dante.VOCABULARY_URI_BASE}/{settings.FileImport.DOCUMENT_TYPE_VOCABULARY_NAME}/{concept_id}',
        'conceptName': __get_concept_name(concept_id)
    }

def __get_concept_name(concept_id):
    dante_database = DanteDatabase(settings.Dante.HOST_URL)
    concept = dante_database.get(settings.FileImport.DOCUMENT_TYPE_VOCABULARY_NAME, concept_id)
    if concept is None:
        raise ValueError(f'{messages.FileImport.ERROR_DOCUMENT_TYPE_CONCEPT_NOT_FOUND} {concept_id}')
    return concept['prefLabel']['de']

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

def __get_document_object(document_type_concept, description, date, fylr):
    return fylr.get_object_by_field_values(
        'dokumente_manuell',
        {
            'typ.conceptURI': document_type_concept['conceptURI'],
            'beschreibung': description,
            'datum': date
        })

def __update_document_object(document, cloned_asset, person, fylr):
    data = document['dokumente_manuell']
    data['datei'] = cloned_asset
    data['lk_bearbeiter'] = person
    fylr.update_object('dokumente_manuell', data['_id'], data)

def __create_document_object(cloned_asset, document_type_concept, person, description, date, vorgang, fylr):
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

    return fylr.create_object('dokumente_manuell', object, pool=vorgang['vorgang']['_pool'])

def __add_document_to_vorgang(document, vorgang, fylr):
    entry = { 'lk_dokument': document }
    data = vorgang['vorgang']

    if data.get('_nested:vorgang__dokumente', None) is None:
        data['_nested:vorgang__dokumente'] = []
    data['_nested:vorgang__dokumente'].append(entry)

    fylr.update_object('vorgang', data['_id'], data)
