import json
from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model import Position
from binance_f.model.constant import *


def run(client: RequestClient, payload: dict):
    result: List[object] = client.get_account_trades(symbol=f"{payload.get('symbol')}USDT")
    pos = [r.__dict__ for r in result]
    return pos
