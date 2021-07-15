import json
from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model import Position, LeverageBracket
from binance_f.model.constant import *
from binance_f.model.leveragebracket import Bracket
from market.Symbol import Symbol


def run(client: RequestClient, payload: dict):
    result: list = client.get_leverage_bracket()
    PrintMix.print_data(result)
    return [s.__json__ for s in result]


def find_leverage_bracket(client: RequestClient, pos: Position) -> Bracket:
    result: List[LeverageBracket] = client.get_leverage_bracket()
    for r in result:
        if r.symbol != pos.symbol:
            continue
        return _get_bracket(r.brackets, pos)
    raise TypeError(f'not find Bracket' + str(pos.__dict__))



def _get_bracket(bs: List[Bracket], pos: Position) -> Bracket:
    bs.sort(key=lambda s: s.initialLeverage)
    for b in bs:
        print(b)
        if pos.leverage <= b.initialLeverage:
            return b
    raise TypeError(f'not find Bracket' + str(pos.__dict__))
