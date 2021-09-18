from typing import List

from binance_f.model import Position
from market.Symbol import Symbol


class PositionFilter:

    def __init__(self, symbol: str = None, positionSide: str = None):
        self.symbol = symbol
        self.positionSide = positionSide

    def get_symbole(self) -> Symbol:
        return Symbol.get(self.symbol)


def filter_position(ps: List[Position], ft: PositionFilter) -> List[Position]:
    ans: List[Position] = list()
    for p in ps:

        if ft.symbol and ft.get_symbole().gen_with_usdt() != p.symbol:
            continue
        if ft.positionSide and ft.positionSide != p.positionSide:
            continue
        ans.append(p)
    return ans


def get_abs_amt(p: Position) -> float:
    return abs(p.positionAmt)

