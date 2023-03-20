from app import settings
from app.field.hub import FieldHub


def update(logger):
    field_hub = FieldHub(settings.Couch.HOST_URL,
                settings.FieldHub.TEMPLATE_PROJECT_NAME,
                auth_from_module=True,
                logger=logger)
    field_hub.update_valuelists()
