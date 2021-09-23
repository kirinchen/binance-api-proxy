from typing import List

from binance_f.model import Order


class PositionStopDto:

    def __init__(self):
        pass


class StopResult:

    def __init__(self, orders: List[Order] = list(), active: bool = False, noActiveMsg: str = None):
        self.active = active
        self.orders: List[Order] = orders
        self.noActiveMsg: str = noActiveMsg
