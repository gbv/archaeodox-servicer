from flask import Flask, request as incoming_request
from easydb_client import EasydbClient
import requests
from dpath import util as dp

app = Flask(__name__)


#@app.route('/', defaults={'n':10})
#@app.route('/<int:n>')
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


def query_easydb(token, search):
    params = {'token': token}
    response = requests.post("http://easydb-webfrontend/api/v1/search",
                             params=params,
                             data=search)


@app.route("/dump", methods=["GET", "POST"])
def dump():
    if incoming_request.method == "POST":
        jason = incoming_request.get_json()
        app.logger.debug("In dump, got jason:" + str(jason))
        session = jason["session"]
        app.logger.debug(str(session))
        client = EasydbClient("http://easydb-webfrontend")

        app.logger.debug(str(client.get_item("teller", "15")))
        return jason.get("data", {}), 200
