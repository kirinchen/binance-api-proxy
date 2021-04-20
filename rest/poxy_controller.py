import json
import os
from enum import Enum
from os import environ

from flask import Flask, Response
from flask import request

from binance_f import RequestClient

import importlib.util


class PayloadReqKey(Enum):
    name = 'name'
    apiKey = 'apiKey'
    secret = 'secret'

    @classmethod
    def values(cls):
        ans = [e for e in PayloadReqKey]
        return ans

    @classmethod
    def clean_default_keys(cls, payload: dict):
        for k in PayloadReqKey.values():
            del payload[k.value]


app = Flask(__name__)


@app.route('/')
def index():
    return f"Hello, World! "


@app.route('/proxy', methods=['POST'])
def proxy():
    payload = request.json
    client = _gen_request_client(payload)
    wd_path = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("action", f"{wd_path}/{payload.get(PayloadReqKey.name.value)}.py")
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    return Response(json.dumps(foo.run(client, payload)),  mimetype='application/json')


def _gen_request_client(payload: dict) -> RequestClient:
    return RequestClient(api_key=payload.get(PayloadReqKey.apiKey.value),
                         secret_key=payload.get(PayloadReqKey.secret.value))


def get_flask_app():
    return app
