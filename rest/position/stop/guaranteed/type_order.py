import abc
from abc import ABCMeta
from enum import Enum
from typing import List

from binance_f.model import Order, Position
from rest.position.position_order_finder import OrderBuildLeave
from rest.position.stop import position_stop_utils
from utils.order_utils import SubtotalBundle

GUARANTEED_ORDER_TAG = 'gntop'

class GuaranteedType(Enum):
    IDLE = 'IDLE'  # no any Filled or new stop order
    DONE = 'DONE'  # just amt / price is ok and no new order
    CORRECT = 'CORRECT'  # just amt / price + no new order
    CHAOS = 'CHAOS'  # 已處理的 order + 現在的 order 就是不對


class BaseType(Enum):
    IDLE = 'IDLE'  # no any Filled or new stop order
    CORRECT = 'CORRECT'  # just amt / price is ok and no new order
    CHAOS = 'CHAOS'  # 現在的 order 就是不對


class TypeOrderHandle(metaclass=ABCMeta):

    def __init__(self):
        self.currentOrders: List[Order] = list()
        self.doneOrders: List[Order] = list()

    @abc.abstractmethod
    def is_conformable(self) -> bool:
        return not self.no_position

    @abc.abstractmethod
    def is_up_to_date(self) -> bool:
        return NotImplemented


class GuaranteedOrderHandle(TypeOrderHandle):

    def __init__(self, guaranteed_price: float, guaranteed_amt: float):
        super(GuaranteedOrderHandle, self).__init__()
        self.guaranteed_price: float = guaranteed_price
        self.guaranteed_amt: float = guaranteed_amt

    def is_up_to_date(self) -> bool:
        """
        True : 有 new stop order
        False : 有
        False : 沒有 或是 stop order 不正確
        """
        if len(self.currentOrders) <= 0 and len(self.doneOrders) <= 0:
            return False
        currentOrdersInfo = SubtotalBundle(orders=self.currentOrders)
        currentOrdersInfo.subtotal()
        doneOrdersInfo = SubtotalBundle(orders=self.doneOrders)
        doneOrdersInfo.subtotal()
        sum_amt = currentOrdersInfo.origQty + doneOrdersInfo.origQty



class BaseOrderHandle(TypeOrderHandle):

    def __init__(self):
        super(BaseOrderHandle, self).__init__()


class HandleBundle:

    def __init__(self, guaranteed: GuaranteedOrderHandle, base: BaseOrderHandle):
        self.guaranteed: GuaranteedOrderHandle = guaranteed
        self.base: BaseOrderHandle = base


def gen_type_order_handle(position: Position,
                          currentStopOrdersInfo: SubtotalBundle,
                          buildLeaveOrderInfo: OrderBuildLeave,
                          guaranteed_price: float,
                          guaranteed_amt: float) -> HandleBundle:
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

    return HandleBundle(
        guaranteed=guaranteed,
        base=base
    )
