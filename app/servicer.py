import requests
import json
import settings
import traceback

from flask import Flask, request as incoming_request
from easydb_client import EasydbClient
from wfs_client import WFSClient
from dpath import util as dp

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


@app.route("/dump", methods=["GET", "POST"])
def dump():
    if incoming_request.method == "POST":
        incoming = incoming_request.get_json()
        info = incoming.get("info", {})
        app.logger.debug("In dump, got info:" + str(info))
        token = incoming['session']['token']
        try:
            payload = info['data']

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

            info['data'] = payload
            return info, 200
        except Exception as e:
            app.logger.error(str(e))
            app.logger.error(traceback.format_exc(e))
            raise e

