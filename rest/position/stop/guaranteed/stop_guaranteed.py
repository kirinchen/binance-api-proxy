from enum import Enum
from typing import List, Generic

from binance_f import RequestClient
from binance_f.model import Order
from rest.position.position_order_finder import PositionOrderFinder, OrderBuildLeave
from rest.position.stop import position_stop_utils
from rest.position.stop.dto import StopResult
from rest.position.stop.position_stop_utils import StopState, GuaranteedBundle
from rest.position.stop.stoper import StopDto, Stoper
from utils.comm_utils import to_dict
from utils.order_utils import SubtotalBundle


class StopOrder:

    def __init__(self):
        self.base: List[Order] = list()
        self.guaranteed: List[Order] = list()


class StopGuaranteedDto(StopDto):
    def __init__(self, symbol: str, positionSide: str, closeRate: float, tags: List[str] = list()):
        super().__init__(symbol=symbol, positionSide=positionSide, tags=tags)
        self.closeRate: float = closeRate


class GuaranteedType(Enum):
    IDLE = 'IDLE'  # no any Filled or new stop order
    DONE = 'DONE'  # just amt / price is ok and no new order
    CORRECT = 'CORRECT'  # just amt / price + no new order
    CHAOS = 'CHAOS'  # 已處理的 order + 現在的 order 就是不對


class GuaranteedOrders:

    def __init__(self):
        self.currentOrders:List[Order] = list()
        self.doneOrders:List[Order] = list()

class BaseType(Enum):
    IDLE = 'IDLE'  # no any Filled or new stop order
    CORRECT = 'CORRECT'  # just amt / price is ok and no new order
    CHAOS = 'CHAOS'  # 現在的 order 就是不對


class StopGuaranteed(Stoper):

    def __init__(self, client: RequestClient, dto: StopGuaranteedDto):
        super().__init__(client=client, state=StopState.GUARANTEED, dto=dto)
        self.stopPrice: float = None
        self.orderFinder: PositionOrderFinder = None
        self.guaranteed_price: float = None
        self.guaranteed_amt: float = None
        self.orderFinder: PositionOrderFinder = None
        self.buildLeaveOrderInfo: OrderBuildLeave = None

    def load_vars(self):
        super().load_vars()
        self.orderFinder = PositionOrderFinder(client=self.client, position=self.position)
        self.buildLeaveOrderInfo = self.orderFinder.get_build_order_info()
        self.stopPrice: float = self._calc_stop_price()
        self.orderFinder: PositionOrderFinder = PositionOrderFinder(client=self.client, position=self.position)
        self.guaranteed_price: float = position_stop_utils.calc_guaranteed_price(self.position.positionSide,
                                                                                 self._gen_guaranteed_bundle())
        self.guaranteed_amt: float = self.buildLeaveOrderInfo.build * self.dto.closeRate

    def is_conformable(self) -> bool:
        if not super().is_conformable():
            return False
        return position_stop_utils.is_valid_stop_price(self.position, self.lastPrice, self.guaranteed_price)

    def stop(self) -> StopResult:
        ods = self.orderFinder.orders
        return to_dict(ods)

    def is_up_to_date(self) -> bool:
        pass

    def clean_old_orders(self) -> List[Order]:
        pass

    def _gen_guaranteed_bundle(self) -> GuaranteedBundle:
        return GuaranteedBundle(
            closeRate=self.dto.closeRate,
            lever=self.position.leverage,
            amount=self.buildLeaveOrderInfo.build.executedQty,
            price=self.buildLeaveOrderInfo.build.avgPrice
        )

    def _calc_stop_price(self) -> float:
        build: SubtotalBundle = self.buildLeaveOrderInfo.build
        guard_balance = (build.avgPrice * build.executedQty) / self.position.leverage
        return position_stop_utils.clac_guard_price(self.position, guard_balance)

    def _get_current_stop_order_info(self) -> StopOrder:
        ans = StopOrder()
        for od in self.currentStopOrdersInfo.orders:
            if position_stop_utils.is_valid_stop_price(self.position, self.buildLeaveOrderInfo.build.avgPrice,
                                                       od.avgPrice):
                ans.base.append(od)
            else:
                ans.guaranteed.append(od)
        return ans

    def _is_match_stop(self) -> bool:
        if
            if self.currentStopOrdersInfo.executedQty <= 0:
                return False
        if position_stop_utils.is_difference_over_range(self.stopPrice, self.currentStopOdAvgPrice, 0.00001):
            return False
        amt: float = self.buildLeaveOrderInfo.build.executedQty * (1 - self.dto.closeRate)
        if position_stop_utils.is_difference_over_range(amt, self.currentStopOrdersInfo.executedQty):
            return False
        return True

