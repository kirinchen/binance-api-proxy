from typing import List

from binance_f import RequestClient
from binance_f.model import Position, AccountInformation
from market.Symbol import Symbol
from rest import post_order
from rest.position.stop import position_stop_utils
from rest.position.stop.position_stop_utils import StopState
from utils import position_utils
from utils.order_utils import SubtotalBundle
from utils.position_utils import PositionFilter, filter_position


class StopLossDto:

    def __init__(self, symbol: str, positionSide: str, balanceRate: float, restopRate: float, tags: List[str] = list()):
        self.balanceRate: float = balanceRate
        self.symbol: str = symbol
        self.positionSide: str = positionSide
        self.restopRate: float = restopRate
        self.tags: List[str] = tags

    def get_symbol(self) -> Symbol:
        return Symbol.get(self.symbol)


class StopLoss:

    def __init__(self, client: RequestClient, dto: StopLossDto):
        self.state: StopState = StopState.LOSS
        self.client: RequestClient = client
        self.dto: StopLossDto = dto
        self.position = self.get_current_position()
        self.no_position = position_utils.get_abs_amt(self.position) <= 0
        if self.no_position:
            return
        self.tags = self._setup_tags(dto.tags)
        (self.currentStopOds, self.currentStopOdAvgPrice) = position_stop_utils.get_current_new_stop_orders(self.client,
                                                                                                            self.position)
        self.stopPrice: float = self.get_stop_quote()

    def _setup_tags(self, tags: List[str]) -> List[str]:
        tags.append(self.state)
        return tags

    def get_current_position(self) -> Position:
        result: List[Position] = self.client.get_position()
        pf = PositionFilter(symbol=self.dto.symbol, positionSide=self.dto.positionSide)
        result = filter_position(result, pf)
        return result[0]

    def get_account(self) -> AccountInformation:
        return self.client.get_account_information()

    def get_stop_quote(self):
        amount = self.get_account().maxWithdrawAmount
        guard_amt = amount * self.dto.balanceRate
        return position_stop_utils.clac_guard_price(self.position, guard_amt)

    def _is_restop_order(self):
        if self.no_position:
            return False
        if position_utils.get_abs_amt(self.position.positionAmt) != self.currentStopOds.executedQty:
            return True
        if position_stop_utils.is_difference_over_range(self.stopPrice, self.currentStopOdAvgPrice,
                                                        self.dto.restopRate):
            return True
        return False

    def stop(self):
        if self._is_restop_order():
            self.post_order()

    def post_order(self):
        post_order.post_stop_order(client=self.client
                                   , tags=self.tags
                                   , stop_side=position_stop_utils.get_stop_order_side(self.position.positionSide)
                                   , symbol=self.dto.get_symbol()
                                   , quantity=position_utils.get_abs_amt(self.position)
                                   , stopPrice=self.stopPrice
                                   )
