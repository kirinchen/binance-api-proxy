from enum import Enum
from typing import List

from binance_f import RequestClient
from rest.position.position_order_finder import PositionOrderFinder
from rest.position.stop import position_stop_utils
from rest.position.stop.dto import StopResult
from rest.position.stop.position_stop_utils import StopState
from rest.position.stop.stoper import StopDto, Stoper
from utils.comm_utils import to_dict


class StopGuaranteedDto(StopDto):
    def __init__(self, symbol: str, positionSide: str, closeRate: float, tags: List[str] = list()):
        super().__init__(symbol=symbol, positionSide=positionSide, tags=tags)
        self.closeRate: float = closeRate


class StopGuaranteed(Stoper):

    def __init__(self, client: RequestClient, dto: StopGuaranteedDto):
        super().__init__(client=client, state=StopState.GUARANTEED, dto=dto)
        if self.no_position:
            return
        self.stopPrice: float = position_stop_utils.calc_guaranteed_price(self.position, self.dto.closeRate)
        self.orderFinder: PositionOrderFinder = PositionOrderFinder(client=self.client, position=self.position)
        self.guaranteed_price: float = position_stop_utils.calc_guaranteed_price(self.position, dto.closeRate)

    def is_conformable(self) -> bool:
        if not super().is_conformable():
            return False
        return position_stop_utils.is_valid_stop_price(self.position, self.lastPrice, self.guaranteed_price)

    def stop(self) -> StopResult:
        ods = self.orderFinder.orders
        return to_dict(ods)
