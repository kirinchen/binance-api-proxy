from abc import ABCMeta
from enum import Enum
from typing import List

from binance_f.model import Order


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


class GuaranteedOrderHandle(TypeOrderHandle):

    def __init__(self):
        super(GuaranteedOrderHandle, self).__init__()


class BaseOrderHandle(TypeOrderHandle):

    def __init__(self):
        super(BaseOrderHandle, self).__init__()


class HandleBundle:

    def __init__(self):
        self.guaranteed = GuaranteedOrderHandle()
        self.base = BaseOrderHandle()


def gen_type_order_handle() -> HandleBundle:
    return None