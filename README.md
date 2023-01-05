# Servicer- the swiss army knife for your easydb

This is the other end of the [servicer client plugin](https://github.com/chris-jan-trapp/easydb-servicer-client-plugin).
It had been intended to break free from the limitations of the python interpreter that comes with easydb5 installations by routing the payload of server callbacks through an external service.
The association between easydb data types and their handling by the servicer is pretty much hardcoded in the last ten lines of [app/servicer.py] and all functionality is also part of the codebase.
A more flexible plugin system can be built when someone finds a second use case for this.

## Components

Tha said, it is kind of modular and comes with some useful parts.

- [app/couch.py] is a client for couchdbs with some added functions for user and database creation, cloning of configuration and such.
- [app/field_client.py] provides a specialised couchdb client to work with the databases on an iDAI.field hub.
- [app/easydb_client.py] helps you with handling object in an easydb and provides session management. It also helps with downloading media files.
- [app/wfs_client.py] lets you handle geometries on a WFS

