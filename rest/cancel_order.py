from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *
from market.Symbol import Symbol

# request_client = RequestClient(api_key=g_api_key, secret_key=g_secret_key)
# result = request_client.cancel_order(symbol="BTCUSDT", orderId=534333508)
# PrintBasic.print_obj(result)
from utils import comm_utils

MAX_BATCH_COUNT = 6


class Dto:

    def __init__(self, ids: List[str], symbol: str, **kwargs):
        self.ids: List[str] = ids
        self.symbol: str = symbol

    def get_symbole(self):
        return Symbol.get(self.symbol)


def run(client: RequestClient, payload: dict):
    dto = Dto(**payload)
    count = 0
    batch_ids: List[str] = list()
    results = list()
    for oid in dto.ids:
        count = count + 1
        batch_ids.append(oid)
        if count == MAX_BATCH_COUNT:
            results.extend(client.cancel_list_orders(symbol=dto.get_symbole().gen_with_usdt(),
                                                     orderIdList=batch_ids))
            count = 0
            batch_ids.clear()

    if len(batch_ids) > 0:
        results.extend(client.cancel_list_orders(symbol=dto.get_symbole().gen_with_usdt(),
                                                 orderIdList=batch_ids))

    return comm_utils.to_struct_list(results)


def cancel_order(client: RequestClient, symbol: Symbol, orderId: int):
    client.cancel_order(symbol=f'{symbol.symbol}USDT', orderId=orderId)
