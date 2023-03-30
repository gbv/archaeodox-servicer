# archaeoDox Servicer

This application is part of the archaeoDox system and accepts EasyDB server callbacks redirected by the [servicer client plugin](https://github.com/gbv/archaeodox-easydb-servicer-client-plugin). Its primary purpose is to connect an EasyDB instance with [Field](https://github.com/dainst/idai-field) databases; therefore it needs a [FieldHub](https://github.com/dainst/idai-field/tree/master/server) server instance to run.


## Functions

### Field database creation
For each newly created "Vorgang" object where the vocabulary concept in field "Vorgangskategorie" is a subconcept of a certain configured concept, a Field database is created. The name and password of the Field project are stored in the EasyDB.

### File import
Import files from an EasyDB instance to a Field project.
* Image import
* CSV import
* Shapefile import

### Vocabulary import
Dante vocabularies can be converted to Field valuelists and added to a Field project.


## Setup

1. Clone this repository
2. Copy the file app/settings.py.template to app/settings.py:
```
scp app/settings.py.template app/settings.py
```
3. Fill in the values in app/settings.py
4. Start the servicer with Docker:
```
docker compose up
```
