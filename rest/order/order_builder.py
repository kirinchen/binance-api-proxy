import abc
from abc import ABCMeta
from typing import TypeVar, Generic, List

from binance_f import RequestClient
from binance_f.model import Position, Order
from market.Symbol import Symbol
from rest.order.dto import BaseDto
from utils import position_utils
from utils.position_utils import PositionFilter


class PriceQty:

    def __init__(self, price: float, quantity: float):
        self.price: float = price
        self.quantity: float = quantity


class LoadDataCheck:

    def __init__(self, success: bool, failsMsg: str = None):
        self.success: bool = success
        self.failsMsg: str = failsMsg


T = TypeVar('T', bound=BaseDto)


class BaseOrderBuilder(Generic[T], metaclass=ABCMeta):

    def __init__(self, client: RequestClient, dto: T):
        self.client: RequestClient = client
        self.dto: T = dto

    def get_current_position(self) -> Position:
        result: List[Position] = self.client.get_position()
        pf = PositionFilter(symbol=self.dto.symbol, positionSide=self.dto.positionSide)
        result = position_utils.filter_position(result, pf)
        return result[0]

    def post(self) -> List[Order]:
        ans: List[Order] = list()
        for pq in self.gen_price_qty_list():
            ans.append(self.post_one(pq))
        return ans

    @abc.abstractmethod
    def load_data(self) -> LoadDataCheck:
        return NotImplemented

    @abc.abstractmethod
    def get_order_side(self) -> str:
        return NotImplemented

    @abc.abstractmethod
    def gen_price_qty_list(self) -> List[PriceQty]:
        return NotImplemented

    @abc.abstractmethod
    def post_one(self, pq: PriceQty) -> Order:
        return NotImplemented
