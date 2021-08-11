OBJECT_TYPE = "teller"
GEO_SERVER_URL = "https://geodienste.gbv.de/nld/wfs"
GEOMETRY = "found_at"
ATTRIBUTES = ["text", ]

RETURN = "feature_id"
CONVERSION_URL = "http://converter:5000/gml/"

TRANSACTION_ATTRIBUTES = {"version": "1.1.0",
                          "service": "WFS",
                          "xmlns": "http://esx-170.gbv.de:8080/geoserver/gbv",
                          "xmlns:gbv": "gbv",
                          "xmlns:gml": "http://www.opengis.net/gml",
                          "xmlns:ogc": "http://www.opengis.net/ogc",
                          "xmlns:wfs": "http://www.opengis.net/wfs",
                          "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
                          "xsi:schemaLocation": """http://esx-170.gbv.de:8080/geoserver/
                                                   http://www.opengis.net/wfs
                                                   ../wfs/1.1.0/WFS.xsd"""
                          }
