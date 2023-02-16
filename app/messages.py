class FileImportingHandler:
    SUCCESS = 'OK'
    ERROR_MISSING_CREDENTIALS = 'Die Verbindung zur Field-Datenbank konnte nicht hergestellt werden. Bitte geben Sie einen Datenbanknamen und das korrekte Passwort an.'
    ERROR_INVALID_FILE_FORMAT = 'Die Datei konnte nicht importiert werden: Die Dateiendung entspricht nicht dem erkannten Dateiformat.'
    ERROR_UNSUPPORTED_FILE_FORMAT = 'Die Datei konnte nicht importiert werden: Das Dateiformat wird nicht unterstützt.'