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
from utils import position_utils, direction_utils
from utils.comm_utils import to_dict
from utils.order_utils import OrdersInfo


class StopOrder:

    def __init__(self):
        self.base: List[Order] = list()
        self.guaranteed: List[Order] = list()


class StopGuaranteedDto(StopDto):
    def __init__(self, symbol: str, positionSide: str, closeRate: float, thresholdRate: float,
                 tags: List[str] = list()):
        super().__init__(symbol=symbol, positionSide=positionSide, tags=tags)
        self.closeRate: float = closeRate
        self.thresholdRate: float = thresholdRate


class StopGuaranteed(Stoper[StopGuaranteedDto]):

    def __init__(self, client: RequestClient, dto: StopGuaranteedDto):
        super().__init__(client=client, state=StopState.GUARANTEED, dto=dto)
        self.stopPrice: float = None
        self.stopAmt: float = None
        self.guaranteed_price: float = None
        self.guaranteed_amt: float = None
        self.orderHandleBundle: type_order.HandleBundle = None

    def load_vars(self):
        super().load_vars()
        self.stopPrice: float = self._calc_stop_price()
        self.guaranteed_price: float = position_stop_utils.calc_guaranteed_price(self.position.positionSide,
                                                                                 self._gen_guaranteed_bundle())
        self.guaranteed_amt: float = position_utils.get_abs_amt(self.position) * self.dto.closeRate
        self.stopAmt: float = position_utils.get_abs_amt(self.position) - self.guaranteed_amt
        self.orderHandleBundle = type_order.gen_type_order_handle(**self.__dict__)

    def is_conformable(self) -> bool:
        if not super().is_conformable():
            return False
        p: float = direction_utils.rise_price(self.position.positionSide, self.guaranteed_price, self.dto.thresholdRate)

        return position_stop_utils.is_valid_stop_price(self.position, self.lastPrice, p)

    def stop(self) -> StopResult:
        ods: List[Order] = list()
        if not self.orderHandleBundle.guaranteed.is_up_to_date():
            ods.extend(self.orderHandleBundle.guaranteed.post_order(client=self.client, tags=self.tags))
        if not self.orderHandleBundle.base.is_up_to_date():
            ods.extend(self.orderHandleBundle.base.post_order(client=self.client, tags=self.tags))
        return StopResult(orders=ods, active=True, stopState=self.state)

    def is_up_to_date(self) -> bool:
        if not self.orderHandleBundle.guaranteed.is_up_to_date():
            return False
        if not self.orderHandleBundle.base.is_up_to_date():
            return False
        return True

    def clean_old_orders(self) -> List[Order]:
        ans: List[Order] = list()
        if not self.orderHandleBundle.guaranteed.is_up_to_date():
            ans.extend(self.orderHandleBundle.guaranteed.clean_old_orders(client=self.client))
        if not self.orderHandleBundle.base.is_up_to_date():
            ans.extend(self.orderHandleBundle.base.clean_old_orders(client=self.client))
        return ans

    def _gen_guaranteed_bundle(self) -> GuaranteedBundle:
        return GuaranteedBundle(
            closeRate=self.dto.closeRate,
            lever=self.position.leverage,
            amount=position_utils.get_abs_amt(self.position),
            price=self.position.entryPrice
        )

    def _calc_stop_price(self) -> float:
        amt: float = position_utils.get_abs_amt(self.position)
        guard_balance = (self.position.entryPrice * amt) / self.position.leverage
        return position_stop_utils.clac_guard_price(self.position, guard_balance)
