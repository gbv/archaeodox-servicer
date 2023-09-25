from app import settings, messages
from app.dante.database import DanteDatabase


def run(cloned_asset, document_type_concept_id, user_name, pool, fylr):
    person = __get_person(user_name, fylr)
    document_type_concept = __get_document_type_concept(document_type_concept_id)
    __create_fylr_object(cloned_asset, document_type_concept, person, pool, fylr)

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

def __get_concept_name(concept_id):
    dante_database = DanteDatabase(settings.Dante.HOST_URL)
    concept = dante_database.get(settings.FileImport.DOCUMENT_TYPE_VOCABULARY_NAME, concept_id)
    if concept is None:
        raise ValueError(f'{messages.FileImport.ERROR_DOCUMENT_TYPE_CONCEPT_NOT_FOUND} {concept_id}')
    return concept['prefLabel']['de']

def __create_fylr_object(cloned_asset, document_type_concept, person, pool, fylr):
    object = {
        'typ': document_type_concept,
        'datei': cloned_asset,
        'lk_bearbeiter': person
    }

    fylr.create_object('dokumente_manuell', object, pool=pool)
