import json
from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model import Order
from binance_f.model.constant import *


def run(client: RequestClient, payload: dict):
    result: List[Order] = client.get_open_orders()
    pos= [r.__dict__ for r in result]
    strs= json.dumps(pos)
    return strs
