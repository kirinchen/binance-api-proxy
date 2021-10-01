import abc
from abc import ABCMeta
from enum import Enum
from typing import List

from binance_f import RequestClient
from binance_f.model import Order, Position
from infr import constant
from market.Symbol import Symbol
from rest import post_order
from rest.position.position_order_finder import OrderBuildLeave
from rest.position.stop import position_stop_utils
from utils import order_utils
from utils.order_utils import OrdersInfo, OrderFilter

GUARANTEED_ORDER_TAG = 'gntop'


class TypeOrderHandle(metaclass=ABCMeta):

    def __init__(self, position: Position):
        self.position: Position = position
        self.currentOrders: List[Order] = list()

    def init_vars(self):
        pass

    @abc.abstractmethod
    def is_up_to_date(self) -> bool:
        return NotImplemented

    @abc.abstractmethod
    def clean_old_orders(self, client: RequestClient) -> List[Order]:
        return NotImplemented

    @abc.abstractmethod
    def post_order(self, client: RequestClient, tags: List[str]) -> List[Order]:
        return NotImplemented


class GuaranteedState(Enum):
    IDLE = 'IDLE'  # no any Filled or new stop order
    DONE = 'DONE'  # just amt / price is ok and no new order
    CORRECT = 'CORRECT'  # just amt / price + no new order
    CHAOS_CURRENT = 'CHAOS_CURRENT'


class GuaranteedOrderHandle(TypeOrderHandle):

    def __init__(self, position: Position, guaranteed_price: float, guaranteed_amt: float):
        super(GuaranteedOrderHandle, self).__init__(position=position)
        self.guaranteed_price: float = guaranteed_price
        self.guaranteed_amt: float = guaranteed_amt
        self.currentStopOrderInfo: OrdersInfo = None

    def init_vars(self):
        self.currentStopOrderInfo: OrdersInfo = order_utils.filter_order(self.currentOrders, OrderFilter(
            tags=[GUARANTEED_ORDER_TAG]
        ))

    def clean_old_orders(self, client: RequestClient) -> List[Order]:
        return position_stop_utils.clean_old_orders(client=client, symbol=Symbol.get_with_usdt(self.position.symbol),
                                             currentOds=self.currentStopOrderInfo.orders)

    def post_order(self, client: RequestClient, tags: List[str]) -> List[Order]:
        return [position_stop_utils.post_stop_order(client=client, tags=tags, position=self.position,
                                                    stopPrice=self.guaranteed_price, quantity=self.guaranteed_amt)]

    def get_state(self) -> GuaranteedState:
        if self.currentStopOrderInfo.origQty <= 0:
            return GuaranteedState.IDLE

        if position_stop_utils.is_difference_over_range(
                self.currentStopOrderInfo.origQty,
                self.guaranteed_amt,
                constant.LIMIT_0_RATE):
            return GuaranteedState.CHAOS_CURRENT
        currentAvgPrice: float = self.currentStopOrderInfo.avgPrice
        return GuaranteedState.CHAOS_CURRENT if position_stop_utils.is_difference_over_range(currentAvgPrice,
                                                                                             self.guaranteed_price,
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

    def __init__(self, position: Position, stopPrice: float, stopAmt: float):
        super(BaseOrderHandle, self).__init__(position=position)
        self.currentStopOrderInfo: OrdersInfo = None
        self.stopPrice: float = stopPrice
        self.stopAmt: float = stopAmt

    def init_vars(self):
        self.currentStopOrderInfo: OrdersInfo = OrdersInfo(orders=self.currentOrders, group=None)
        self.currentStopOrderInfo.subtotal()

    def get_state(self) -> BaseState:
        if self.currentStopOrderInfo.origQty <= 0:
            return BaseState.IDLE
        if position_stop_utils.is_difference_over_range(self.stopPrice, self.currentStopOrderInfo.avgPrice,
                                                        constant.LIMIT_0_RATE):
            return BaseState.CHAOS
        return BaseState.CHAOS if position_stop_utils.is_difference_over_range(
            self.currentStopOrderInfo.origQty,
            self.stopAmt,
            constant.LIMIT_0_RATE) else BaseState.DONE

    def is_up_to_date(self) -> bool:
        state = self.get_state()
        return state == BaseState.DONE

    def clean_old_orders(self, client: RequestClient) -> List[Order]:
        return position_stop_utils.clean_old_orders(client=client, symbol=Symbol.get_with_usdt(self.position.symbol),
                                             currentOds=self.currentStopOrderInfo.orders)

    def post_order(self, client: RequestClient, tags: List[str]) -> List[Order]:
        return [position_stop_utils.post_stop_order(client=client, tags=tags, position=self.position,
                                                    stopPrice=self.stopPrice, quantity=self.stopAmt)]


class HandleBundle:

    def __init__(self, guaranteed: GuaranteedOrderHandle, base: BaseOrderHandle):
        self.guaranteed: GuaranteedOrderHandle = guaranteed
        self.base: BaseOrderHandle = base


def gen_type_order_handle(position: Position,
                          currentStopOrdersInfo: OrdersInfo,
                          guaranteed_price: float,
                          guaranteed_amt: float,
                          stopPrice: float,
                          stopAmt: float, **kwargs) -> HandleBundle:
    base = BaseOrderHandle(position=position, stopPrice=stopPrice, stopAmt=stopAmt)
    guaranteed = GuaranteedOrderHandle(position=position, guaranteed_price=guaranteed_price,
                                       guaranteed_amt=guaranteed_amt)
    for od in currentStopOrdersInfo.orders:
        if position_stop_utils.is_valid_stop_price(position, position.entryPrice, od.stopPrice):
            base.currentOrders.append(od)
        else:
            guaranteed.currentOrders.append(od)


    guaranteed.init_vars()
    base.init_vars()

    return HandleBundle(
        guaranteed=guaranteed,
        base=base
    )
