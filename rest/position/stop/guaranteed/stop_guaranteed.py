from typing import List

from binance_f import RequestClient
from rest.position.stop import position_stop_utils
from rest.position.stop.dto import StopResult
from rest.position.stop.position_stop_utils import StopState
from rest.position.stop.stoper import StopDto, Stoper


class StopGuaranteedDto(StopDto):
    def __init__(self, symbol: str, positionSide: str,  closeRate: float,tags: List[str] = list()):
        super().__init__(symbol=symbol, positionSide=positionSide, tags=tags)
        self.closeRate: float = closeRate


class StopGuaranteed(Stoper):

    def __init__(self, client: RequestClient, dto: StopGuaranteedDto):
        super().__init__(client=client, state=StopState.GUARANTEED, dto=dto)
        self.stopPrice 



    def stop(self) -> StopResult:
        stopPrice: float = position_stop_utils.calc_guaranteed_price(self.position, self.dto.closeRate)
        return {}
