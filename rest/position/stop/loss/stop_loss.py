from typing import List

from binance_f import RequestClient
from binance_f.model import Position, AccountInformation, Order
from market.Symbol import Symbol
from rest import post_order
from rest.position.stop import position_stop_utils
from rest.position.stop.dto import StopResult
from rest.position.stop.position_stop_utils import StopState
from rest.position.stop.stoper import StopDto, Stoper
from utils import position_utils
from utils.order_utils import SubtotalBundle
from utils.position_utils import PositionFilter, filter_position


class StopLossDto(StopDto):

    def __init__(self, symbol: str, positionSide: str, balanceRate: float, restopRate: float, tags: List[str] = list()):
        super().__init__(symbol=symbol, positionSide=positionSide, tags=tags)
        self.balanceRate: float = balanceRate
        self.restopRate: float = restopRate


class StopLoss(Stoper):

    def __init__(self, client: RequestClient, dto: StopLossDto):
        super().__init__(client=client, state=StopState.LOSS, dto=dto)

    def _get_stop_quote(self):
        amount = self.get_account().maxWithdrawAmount
        guard_amt = amount * self.dto.balanceRate
        return position_stop_utils.clac_guard_price(self.position, guard_amt)

    def _is_order_restopable(self):
        if self.no_position:
            return False
        if position_utils.get_abs_amt(self.position) != self.currentStopOrdersInfo.executedQty:
            return True
        if position_stop_utils.is_difference_over_range(self.stopPrice, self.currentStopOdAvgPrice,
                                                        self.dto.restopRate):
            return True
        return False

    def stop(self) -> StopResult:
        ans = StopResult()
        if self._is_order_restopable():
            position_stop_utils.clean_old_orders(client=self.client, symbol=self.dto.get_symbol(),
                                                 currentOds=self.currentStopOrdersInfo.orders)
            ans.orders = [self.post_order()]
            ans.active = True
        return ans

    def is_conformable(self) -> bool:
        if not super().is_conformable():
            return False
        return True

    def post_order(self) -> Order:
        stopPrice: float = self._get_stop_quote()
        return post_order.post_stop_order(client=self.client
                                          , tags=self.tags
                                          ,
                                          stop_side=position_stop_utils.get_stop_order_side(self.position.positionSide)
                                          , symbol=self.dto.get_symbol()
                                          , quantity=position_utils.get_abs_amt(self.position)
                                          , stopPrice=stopPrice
                                          ,
                                          )
