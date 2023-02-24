class FileImport:
    SUCCESS = 'OK'
    ERROR_PREFIX = 'Die Datei konnte nicht importiert werden:'
    ERROR_VORGANG_NOT_IN_FILENAME = 'Der Dateiname muss mit dem Vorgangsnamen beginnen.'
    ERROR_MISSING_CREDENTIALS = 'Die Verbindung zur Field-Datenbank konnte nicht hergestellt werden. Bitte geben Sie einen Vorgangsnamen und das dazugehörige Passwort an.'
    ERROR_INVALID_CREDENTIALS = 'Die Verbindung zur Field-Datenbank konnte nicht hergestellt werden. Bitte prüfen Sie den Vorgangsnamen und das angegebene Passwort.'
    ERROR_INVALID_FILE_FORMAT = 'Die Dateiendung entspricht nicht dem erkannten Dateiformat.'
    ERROR_UNSUPPORTED_FILE_FORMAT = 'Das Dateiformat wird nicht unterstützt.'
    ERROR_SHAPEFILE_INVALID_NAME = 'Im Dateinamen des Shapefiles muss entweder die Zeichenfolge "FLZ" (bei Flächenzeichnungen) oder "PRZ" (für Profile) enthalten sein.'
    ERROR_SHAPEFILE_MISSING_EXCA_INT = 'Das Attribut "exca_int" in der Attributtabelle des Shapefiles muss ausgefüllt sein.'
    ERROR_GEOTIFF_GEOREFERENCE = 'Die Georeferenzierungsdaten konnten nicht ausgelesen werden. Bitte prüfen Sie, ob es sich um eine gültige GeoTIFF-Datei handelt.'
