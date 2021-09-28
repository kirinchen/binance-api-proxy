from typing import List

from binance_f.model import Order
from rest.position.stop.position_stop_utils import StopState


class PositionStopDto:

    def __init__(self):
        pass


class StopResult:

    def __init__(self, stopState: StopState, orders: List[Order] = list(), active: bool = False,
                 noActiveMsg: str = None,
                 up_to_date: bool = False):
        self.active = active
        self.stopState: str = stopState.value
        self.orders: List[Order] = orders
        self.noActiveMsg: str = noActiveMsg
        self.up_to_date: bool = up_to_date
