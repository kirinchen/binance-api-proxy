import json
from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model import Position
from binance_f.model.constant import *
from rest.poxy_controller import PayloadReqKey
from utils.position_utils import PositionFilter, filter_position


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    pf = PositionFilter(**payload)
    result: List[Position] = client.get_position()
    result = filter_position(result, pf)
    pos = [r.__dict__ for r in result]
    return pos
