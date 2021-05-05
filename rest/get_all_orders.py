from datetime import datetime
from typing import Dict, List

import pytz

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model import Order
from binance_f.model.constant import *

# request_client = RequestClient(api_key=g_api_key, secret_key=g_secret_key)
# result = request_client.get_all_orders(symbol="BTCUSDT")
# PrintMix.print_data(result)

# https://github.com/binance/binance-spot-api-docs/blob/master/rest-api.md#enum-definitions
from utils.order_utils import filter_order_by_payload


def run(client: RequestClient, payload: dict):
    limit = payload.get('limit', None)
    if 'limit' in payload:
        del payload['limit']
    result = client.get_all_orders(symbol=payload.get('symbol') + 'USDT', limit=limit)

    return filter_order_by_payload(result, payload)
