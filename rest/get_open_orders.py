import json
from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model import Order
from binance_f.model.constant import *
from market.Symbol import Symbol
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils


class OrderFilter:

    def __init__(self, symbol: str = None, side: str = None, orderType: str = None, tags: List[str] = list()):
        self.symbol = symbol
        self.side = side
        self.tags = tags
        self.orderType = orderType

    def get_symbole(self):
        return Symbol.get(self.symbol)


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    result: List[Order] = client.get_open_orders()
    pl = OrderFilter(**payload)
    result = filter_order(result, pl)
    return comm_utils.to_struct_list(result)


def filter_order(oods: List[Order], ft: OrderFilter) -> List[Order]:
    ans: List[Order] = list()
    for ods in oods:
        if ft.orderType and ods.type != ft.orderType:
            continue
        if ft.side and ods.side != ft.side:
            continue
        if ft.symbol and ft.get_symbole().gen_with_usdt() != ods.symbol:
            continue
        if len(ft.tags) > 0 and not comm_utils.contains_tags(ods.clientOrderId, ft.tags):
            continue
        ans.append(ods)
    return ans
