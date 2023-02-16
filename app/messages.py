class FileImportingHandler:
    SUCCESS = 'OK'
    ERROR_PREFIX = 'Die Datei konnte nicht importiert werden:'
    ERROR_MISSING_CREDENTIALS = 'Die Verbindung zur Field-Datenbank konnte nicht hergestellt werden. Bitte geben Sie einen Vorgangsnamen und das dazugehörige Passwort an.'
    ERROR_INVALID_CREDENTIALS = 'Die Verbindung zur Field-Datenbank konnte nicht hergestellt werden. Bitte prüfen Sie den Vorgangsnamen und das angegebene Passwort.'
    ERROR_INVALID_FILE_FORMAT = 'Die Dateiendung entspricht nicht dem erkannten Dateiformat.'
    ERROR_UNSUPPORTED_FILE_FORMAT = 'Das Dateiformat wird nicht unterstützt.'