from abc import ABCMeta
from enum import Enum
from typing import List, Generic

from binance_f import RequestClient
from binance_f.model import Order
from rest.position.position_order_finder import PositionOrderFinder, OrderBuildLeave
from rest.position.stop import position_stop_utils
from rest.position.stop.dto import StopResult
from rest.position.stop.guaranteed import type_order
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


class StopGuaranteed(Stoper[StopGuaranteedDto]):

    def __init__(self, client: RequestClient, dto: StopGuaranteedDto):
        super().__init__(client=client, state=StopState.GUARANTEED, dto=dto)
        self.stopPrice: float = None
        self.orderedFinder: PositionOrderFinder = None
        self.guaranteed_price: float = None
        self.guaranteed_amt: float = None
        self.orderedFinder: PositionOrderFinder = None
        self.buildLeaveOrderInfo: OrderBuildLeave = None
        self.orderHandleBundle: type_order.HandleBundle = None

    def load_vars(self):
        super().load_vars()
        self.orderedFinder = PositionOrderFinder(client=self.client, position=self.position)
        self.buildLeaveOrderInfo = self.orderedFinder.get_build_leave_order_info()
        self.stopPrice: float = self._calc_stop_price()
        self.guaranteed_price: float = position_stop_utils.calc_guaranteed_price(self.position.positionSide,
                                                                                 self._gen_guaranteed_bundle())
        self.guaranteed_amt: float = self.buildLeaveOrderInfo.build.origQty * self.dto.closeRate
        self.orderHandleBundle = type_order.gen_type_order_handle(**self.__dict__)

    def is_conformable(self) -> bool:
        if not super().is_conformable():
            return False
        return position_stop_utils.is_valid_stop_price(self.position, self.lastPrice, self.guaranteed_price)

    def stop(self) -> StopResult:
        ods = self.orderedFinder.orders
        return to_dict(ods)

    def is_up_to_date(self) -> bool:
        pass

    def clean_old_orders(self) -> List[Order]:
        pass

    def _gen_guaranteed_bundle(self) -> GuaranteedBundle:
        return GuaranteedBundle(
            closeRate=self.dto.closeRate,
            lever=self.position.leverage,
            amount=self.buildLeaveOrderInfo.build.origQty,
            price=self.buildLeaveOrderInfo.build.avgPrice
        )

    def _calc_stop_price(self) -> float:
        build: SubtotalBundle = self.buildLeaveOrderInfo.build
        guard_balance = (build.avgPrice * build.origQty) / self.position.leverage
        return position_stop_utils.clac_guard_price(self.position, guard_balance)


