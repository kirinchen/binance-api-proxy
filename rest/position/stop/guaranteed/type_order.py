import abc
from abc import ABCMeta
from enum import Enum
from typing import List

from binance_f.model import Order, Position
from infr import constant
from rest.position.position_order_finder import OrderBuildLeave
from rest.position.stop import position_stop_utils
from utils import order_utils
from utils.order_utils import SubtotalBundle, OrderFilter

GUARANTEED_ORDER_TAG = 'gntop'


class TypeOrderHandle(metaclass=ABCMeta):

    def __init__(self):
        self.currentOrders: List[Order] = list()
        self.doneOrders: List[Order] = list()

    def init_vars(self):
        pass

    @abc.abstractmethod
    def is_up_to_date(self) -> bool:
        return NotImplemented


class GuaranteedState(Enum):
    IDLE = 'IDLE'  # no any Filled or new stop order
    DONE = 'DONE'  # just amt / price is ok and no new order
    CORRECT = 'CORRECT'  # just amt / price + no new order
    CHAOS_OLD_DONE = 'CHAOS_OLD_DONE'  # 已處理的 order + 現在的 order 就是不對
    CHAOS_CURRENT = 'CHAOS_CURRENT'
    CHAOS_COMBINE = 'CHAOS_COMBINE'


class GuaranteedOrderHandle(TypeOrderHandle):

    def __init__(self, guaranteed_price: float, guaranteed_amt: float):
        super(GuaranteedOrderHandle, self).__init__()
        self.guaranteed_price: float = guaranteed_price
        self.guaranteed_amt: float = guaranteed_amt
        self.currentStopOrderInfo: SubtotalBundle = None
        self.doneStopOrderInfo: SubtotalBundle = None

    def init_vars(self):
        self.currentStopOrderInfo: SubtotalBundle = order_utils.filter_order(self.currentOrders, OrderFilter(
            tags=[GUARANTEED_ORDER_TAG]
        ))
        self.doneStopOrderInfo: SubtotalBundle = order_utils.filter_order(self.doneOrders, OrderFilter(
            tags=[GUARANTEED_ORDER_TAG]
        ))

    def get_state(self) -> GuaranteedState:
        if self.currentStopOrderInfo.origQty <= 0 and self.doneStopOrderInfo.origQty <= 0:
            return GuaranteedState.IDLE
        if self.currentStopOrderInfo.origQty <= 0:
            return GuaranteedState.CHAOS_OLD_DONE if position_stop_utils.is_difference_over_range(
                self.doneStopOrderInfo.origQty,
                self.guaranteed_amt,
                constant.LIMIT_0_RATE) else GuaranteedState.DONE
        if self.doneStopOrderInfo.origQty <= 0:
            return GuaranteedState.CHAOS_CURRENT if position_stop_utils.is_difference_over_range(
                self.currentStopOrderInfo.origQty,
                self.guaranteed_amt,
                constant.LIMIT_0_RATE) else GuaranteedState.DONE
        total_amt = self.currentStopOrderInfo.origQty + self.doneStopOrderInfo.origQty
        return GuaranteedState.CHAOS_COMBINE if position_stop_utils.is_difference_over_range(total_amt,
                                                                                             self.guaranteed_amt,
                                                                                             constant.LIMIT_0_RATE) else GuaranteedState.DONE

    def is_up_to_date(self) -> bool:
        """
        True : 有 Filled 然後是 GUARANTEED_ORDER_TAG 的Order
        False : 有
        False : 沒有 或是 stop order 不正確
        """
        state = self.get_state()
        return state == GuaranteedState.DONE


class BaseState(Enum):
    IDLE = 'IDLE'  # no any Filled or new stop order
    DONE = 'DONE'  # just amt / price is ok and no new order
    CHAOS = 'CHAOS'  # 現在的 order 就是不對


class BaseOrderHandle(TypeOrderHandle):

    def __init__(self):
        super(BaseOrderHandle, self).__init__()
        self.currentStopOrderInfo: SubtotalBundle = None

    def init_vars(self):
        self.currentStopOrderInfo: SubtotalBundle = SubtotalBundle(orders=self.currentOrders,group=None)
        self.currentStopOrderInfo.subtotal()

    def get_state(self) -> BaseState:
        if self.currentStopOrderInfo.origQty <= 0:
            return BaseState.IDLE
        return BaseState.CHAOS if position_stop_utils.is_difference_over_range(
            self.currentStopOrderInfo.origQty,
            self.guaranteed_amt,
            constant.LIMIT_0_RATE) else BaseState.DONE

    def is_up_to_date(self) -> bool:
        state = self.get_state()
        return state == BaseState.DONE


class HandleBundle:

    def __init__(self, guaranteed: GuaranteedOrderHandle, base: BaseOrderHandle):
        self.guaranteed: GuaranteedOrderHandle = guaranteed
        self.base: BaseOrderHandle = base


def gen_type_order_handle(position: Position,
                          currentStopOrdersInfo: SubtotalBundle,
                          buildLeaveOrderInfo: OrderBuildLeave,
                          guaranteed_price: float,
                          guaranteed_amt: float, **kwargs) -> HandleBundle:
    base = BaseOrderHandle()
    guaranteed = GuaranteedOrderHandle(guaranteed_price=guaranteed_price, guaranteed_amt=guaranteed_amt)
    for od in currentStopOrdersInfo.orders:
        if position_stop_utils.is_valid_stop_price(position, position.entryPrice, od.stopPrice):
            base.currentOrders.append(od)
        else:
            guaranteed.currentOrders.append(od)

    for od in buildLeaveOrderInfo.leave.orders:
        if position_stop_utils.is_valid_stop_price(position, position.entryPrice, od.stopPrice):
            base.doneOrders.append(od)
        else:
            guaranteed.doneOrders.append(od)

    guaranteed.init_vars()
    base.init_vars()

    return HandleBundle(
        guaranteed=guaranteed,
        base=base
    )
