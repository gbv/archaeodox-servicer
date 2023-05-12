# archaeoDox Servicer

This application is part of the archaeoDox system and is called by the [archaeoDox Fylr plugin](https://github.com/gbv/archaeodox-fylr-plugin). Its primary purpose is to connect a Fylr instance with [Field](https://github.com/dainst/idai-field) databases; therefore it needs a [FieldHub](https://github.com/dainst/idai-field/tree/master/server) server instance to run.


## Functions

### Field database creation
For each newly created "Vorgang" object where the vocabulary concept in field "Vorgangskategorie" is a subconcept of a certain configured concept, a Field database is created. The name and password of the Field project are stored in the Fylr database.

### File import
Import files from a Fylr instance to a Field project.
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
4. Replace the network name in docker-compose.yml (networks -> hostnet -> name) with the name of the network used by Fylr
5. Start the servicer with Docker:
```
docker compose up
```
