import json
import os
from contextlib import contextmanager
from datetime import datetime
from enum import Enum
import logging

from flask import Flask, Response
from flask import request

from binance_f import RequestClient, SubscriptionClient

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
    return f"Hello, World! BA"


@app.route('/log')
def log():
    filepath = '/tmp/{:%Y-%m-%d}.log'.format(datetime.now())
    enc = 'utf-8'
    with open(filepath, encoding=enc) as fp:
        ctn = fp.read()
        return ctn


@app.route('/log', methods=['DELETE'])
def del_log():
    filepath = '/tmp/srv.log'
    filehandler_dbg = logging.FileHandler(filepath, mode='w')


@app.route('/proxy', methods=['POST'])
def proxy():
    payload = request.json
    client = _gen_request_client(payload)
    wd_path = os.path.dirname(__file__)
    spec = importlib.util.spec_from_file_location("action", f"{wd_path}/{payload.get(PayloadReqKey.name.value)}.py")
    foo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(foo)
    return Response(json.dumps(foo.run(client, payload)), mimetype='application/json')


def _gen_request_client(payload: dict) -> RequestClient:
    return RequestClient(api_key=payload.get(PayloadReqKey.apiKey.value),
                         secret_key=payload.get(PayloadReqKey.secret.value))


@contextmanager
def gen_ws_client(payload: dict) -> SubscriptionClient:
    sub_client = SubscriptionClient(api_key=payload.get(PayloadReqKey.apiKey.value),
                                    secret_key=payload.get(PayloadReqKey.secret.value))
    try:
        yield sub_client
    finally:
        sub_client.unsubscribe_all()


def get_flask_app():
    return app
