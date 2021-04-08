from binance_f import RequestClient
from rest.poxy_controller import PayloadReqKey


def run(client: RequestClient, payload: dict):
    for k in PayloadReqKey.values():
        del payload[k.value]
    _test(**payload)
    client.post_order()
    return {}


def _test(a:str,b:int,c:str):
    print(f'{a}{b}{c}')