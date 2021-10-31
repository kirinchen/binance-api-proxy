from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model import Order
from binance_f.model.constant import *
from market.Symbol import Symbol

# request_client = RequestClient(api_key=g_api_key, secret_key=g_secret_key)
# result = request_client.cancel_order(symbol="BTCUSDT", orderId=534333508)
# PrintBasic.print_obj(result)
from utils import comm_utils

MAX_BATCH_COUNT = 6


class Dto:

    def __init__(self, symbol: str, origClientOrderIdList: List[str] = None, ids: List[str] = None, **kwargs):
        self.ids: List[str] = ids
        self.origClientOrderIdList: List[str] = origClientOrderIdList
        self.symbol: str = symbol

    def get_symbole(self):
        return Symbol.get(self.symbol)


def run(client: RequestClient, payload: dict):
    dto = Dto(**payload)
    count = 0
    client_id_ble: bool = dto.origClientOrderIdList is not None
    ids: List[str] = dto.origClientOrderIdList if client_id_ble else dto.ids
    batch_ids: List[str] = list()
    results = list()
    for oid in ids:
        count = count + 1
        batch_ids.append(oid)
        if count == MAX_BATCH_COUNT:
            results.extend(_cancel_list_orders(client=client, symbol=dto.get_symbole(), client_id_ble=client_id_ble,
                                               batch_ids=batch_ids))

            count = 0
            batch_ids.clear()

    if len(batch_ids) > 0:
        results.extend(_cancel_list_orders(client=client, symbol=dto.get_symbole(), client_id_ble=client_id_ble,
                                           batch_ids=batch_ids))

    return comm_utils.to_struct_list(results)


def _cancel_list_orders(client: RequestClient, symbol: Symbol, client_id_ble: bool, batch_ids: List[str]) -> Order:
    if client_id_ble:
        return client.cancel_list_orders(symbol=symbol.gen_with_usdt(),
                                         origClientOrderIdList=batch_ids)
    else:
        return client.cancel_list_orders(symbol=symbol.gen_with_usdt(),
                                         orderIdList=batch_ids)


def cancel_order(client: RequestClient, symbol: Symbol, orderId: int):
    client.cancel_order(symbol=f'{symbol.symbol}USDT', orderId=orderId)
