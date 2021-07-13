import json
from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model import Position
from binance_f.model.constant import *


def run(client: RequestClient, payload: dict):
    result: list = client.get_leverage_bracket()
    return [s.__json__ for s in result]
