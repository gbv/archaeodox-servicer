import http
import requests
import json
import traceback

from flask import Flask, request as incoming_request
from .easydb_client import EasydbClient, EASLiberator
from .wfs_client import WFSClient
from dpath import util as dp

from .dante_field.couch import Client as CouchClient
from . import settings

app = Flask(__name__)
edb = EasydbClient("http://easydb-webfrontend", app.logger)

wfs = WFSClient(settings.GEO_SERVER_URL,
                settings.TRANSACTION_ATTRIBUTES,
                settings.OBJECT_TYPE,
                settings.OBJECT_NAMESPACE,
                settings.ATTRIBUTES,
                settings.GEOMETRY,
                app.logger)


@app.route('/', defaults={'n':10})
@app.route('/<int:n>')
def root(n):
    params = {'num': n,
              'min': 1,
              'max': 20,
              'base': '10',
              'md': 'new',
              'format': 'plain',
              'col': 1}
    headers = {'user-agent': 'christian.trapp@gbv.de'}
    r = requests.get("https://random.org/integers/",
                     params=params,
                     headers=headers)
    if r.status_code == 200:
        return r.text
    else:
        return r.url, 'failed'


def get_wfs_id(item_type, id, token):
    result, code = edb.get_item(item_type, id, token=token)
    app.logger.debug("Got items: " + json.dumps(result, indent=2))
    return dp.get(result, [item_type, "feature_id"])


@app.route("/pre-update/parked", methods=["GET", "POST"])
def pre_update():
    if incoming_request.method == "POST":
        incoming_json = incoming_request.get_json()
        
        try:
            payload = incoming_json['data']
            token = incoming_json['session']['token']
            
            relevant_objects = filter(lambda o: settings.OBJECT_TYPE in o.keys(), payload)
            if not relevant_objects:
                return info, 200

            for relevant_object in relevant_objects:
                index = payload.index(relevant_object)
                unpacked = relevant_object[settings.OBJECT_TYPE]
                app.logger.debug('Handling relevant object: ' + settings.OBJECT_TYPE + str(unpacked))
                keys = unpacked.keys()
                has_geometry = settings.GEOMETRY in keys
                created = unpacked.get("_id") is None
                if created and has_geometry:
                    app.logger.debug("Attempting CREATE")
                    id = wfs.create_feature(unpacked)
                    payload[index][settings.OBJECT_TYPE][settings.RETURN] = id
                else:
                    app.logger.debug("Attempting UPDATE")
                    wfs_id = get_wfs_id(settings.OBJECT_TYPE, unpacked['_id'], token)
                    data = wfs.update_feature(unpacked, wfs_id)
                    app.logger.debug(data)

            return {'data': payload}, 200
        except Exception as e:
            app.logger.error(str(e))
            app.logger.error(traceback.format_exc(e))
            raise e


@app.route("/post-update", methods=["POST"])
def post_update():
     if incoming_request.method == "POST":
        incoming = incoming_request.get_json()
        app.logger.debug("In post-update, got incoming:\n" + json.dumps(incoming, indent=2))
        try:
            token = incoming['session']['token']
            data = incoming['data']
            object_type = data['_objecttype']
            id = data[object_type]['_id']
            mask = data['_mask']
            item, status = edb.get_item(item_type=object_type, id=id, token=token)
            app.logger.debug('ITEM:')
            app.logger.debug(item)
            if status == 200:
                liberator = EASLiberator(base_path='/eas', base_url='https://hekate.gbv.de/eas/partitions-inline/1/', logger=app.logger)
                dict_path, source = next(dp.search(incoming, f'**/{object_type}/**/original/url', yielded=True))
                app.logger.debug(source)
                if source:
                    app.logger.debug('ready to liberate')
            return {'data': data}, 200
        except Exception as e:
            app.logger.error(str(e))
            app.logger.error(traceback.format_exc(e))
            return {'error': str(e)}, 500

@app.route('/pre-update', methods=['POST'])
def field_create():
    app.logger.debug(dir(settings))
    if incoming_request.method == "POST":
        incoming_json = incoming_request.get_json()
        
        try:
            data = incoming_json['data']
            token = incoming_json['session']['token']
            app.logger.debug('pre-update:')
            app.logger.debug(json.dumps(data, indent=2))
            has_db = False
            for i, entry in enumerate(data):
                if settings.FIELD_FIELD in entry.keys():
                    db_index = i
                    has_db = True
                    break
            if not has_db:
                return {'data': data}, 200
            
            field_database = data[db_index][settings.FIELD_FIELD]
            password = field_database.get('password', False)

            if password:
                return {'data': data}, 200
           
            db_name = field_database['db_name']
            couch_client = CouchClient(settings.COUCH_HOST, auth_from_env=True)
            db_user = couch_client.create_db_and_user(db_name)
            field_database['password'] = db_user['password']

            return {'data': data}, 200

        except Exception as e:
            app.logger.error(str(e))
            app.logger.error(traceback.format_exc(e))
            return {'error': str(e)}, 500