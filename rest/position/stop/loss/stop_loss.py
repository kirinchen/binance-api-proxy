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
from utils.order_utils import OrdersInfo
from utils.position_utils import PositionFilter, filter_position


class StopLossDto(StopDto):

    def __init__(self, symbol: str, positionSide: str, balanceRate: float, restopRate: float, tags: List[str] = list()):
        super().__init__(symbol=symbol, positionSide=positionSide, tags=tags)
        self.balanceRate: float = balanceRate
        self.restopRate: float = restopRate


class StopLoss(Stoper[StopDto]):

    def __init__(self, client: RequestClient, dto: StopLossDto):
        super().__init__(client=client, state=StopState.LOSS, dto=dto)
        self.stopPrice: float = None

    def load_vars(self):
        super(StopLoss, self).load_vars()
        self.stopPrice = self._get_stop_quote()

    def _get_stop_quote(self):
        amount = self.get_account().maxWithdrawAmount
        guard_amt = amount * self.dto.balanceRate
        return position_stop_utils.clac_guard_price(self.position, guard_amt)

    def is_up_to_date(self) -> bool:
        if position_utils.get_abs_amt(self.position) != self.currentStopOrdersInfo.origQty:
            return False
        return not position_stop_utils.is_difference_over_range(self.stopPrice, self.currentStopOrdersInfo.avgPrice,
                                                                self.dto.restopRate)

    def clean_old_orders(self) -> List[Order]:
        position_stop_utils.clean_old_orders(client=self.client, symbol=Symbol.get_with_usdt(self.position.symbol),
                                             currentOds=self.currentStopOrdersInfo.orders)
        return self.currentStopOrdersInfo.orders

    def stop(self) -> StopResult:
        ans = StopResult(stopState=self.state)
        ans.orders = [self.post_order()]
        ans.active = True
        return ans

    def is_conformable(self) -> bool:
        if not super().is_conformable():
            return False
        return True

    def post_order(self) -> Order:
        return position_stop_utils.post_stop_order(client=self.client, tags=self.tags, position=self.position,
                                                   stopPrice=self.stopPrice,
                                                   quantity=position_utils.get_abs_amt(self.position))
