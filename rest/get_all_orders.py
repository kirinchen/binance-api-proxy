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

def run(client: RequestClient, payload: dict):
    result = client.get_all_orders(symbol=payload.get('symbol') + 'USDT', limit=payload.get('limit', None))
    b = gen_bundle(result)
    # pos = [r.__dict__ for r in result]
    return b.to_struct()


class StatusBundle:
    def __init__(self):
        self.lastAt: datetime = None
        self.orders: List[Order] = list()

    def subtotal(self):
        self.orders.sort(key=lambda s: s.updateTime, reverse=True)
        ups = self.orders[0].updateTime/1000
        self.lastAt = datetime.fromtimestamp(ups,pytz.utc)

    def to_struct(self):
        return {
            'lastAt':self.lastAt.isoformat(),
            'orders': [o.__dict__ for o in self.orders]
        }


class Bundle:
    def __init__(self):
        self.map: Dict[str, StatusBundle] = dict()

    def to_struct(self):
        ans = {}
        for k,v in self.map.items():
            ans[k] = v.to_struct()
        return ans


def gen_bundle(ods: List[Order]) -> Bundle:
    ans = Bundle()
    for od in ods:
        if od.status not in ans.map:
            ans.map[od.status] = StatusBundle()
        ans.map[od.status].orders.append(od)
    for k, v in ans.map.items():
        v.subtotal()
    return ans
