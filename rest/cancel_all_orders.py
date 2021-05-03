from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *

# request_client = RequestClient(api_key=g_api_key, secret_key=g_secret_key)
# result = request_client.cancel_all_orders(symbol="BTCUSDT")
# PrintBasic.print_obj(result)
from market.Symbol import Symbol


def run(client: RequestClient, payload: dict):
    sbl: Symbol = Symbol.get(payload.get('symbol'))
    result = client.cancel_all_orders(symbol=f'{sbl.symbol}USDT')
    return result.__dict__
