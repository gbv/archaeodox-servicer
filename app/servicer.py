from flask import Flask, request as incoming_request
from easydb_client import EasydbClient
import requests
from dpath import util as dp

app = Flask(__name__)
edb = EasydbClient("http://easydb-webfrontend", app.logger)

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


@app.route("/dump", methods=["GET", "POST"])
def dump():
    if incoming_request.method == "POST":
        incoming = incoming_request.get_json()
        info = incoming.get("info", {})
        app.logger.debug("In dump, got info:" + str(info))
        token = incoming['session']['token']
        app.logger.debug("Got item:" + str(edb.get_item("teller", "15", token=token)))
        return info, 200
