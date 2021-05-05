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
from utils.order_utils import OrderFilter, filter_order, filter_order_by_payload


def run(client: RequestClient, payload: dict):
    result: List[Order] = client.get_open_orders()
    return filter_order_by_payload(result, payload)
