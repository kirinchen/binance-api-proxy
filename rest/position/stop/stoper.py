import abc
from abc import ABCMeta
from typing import List, TypeVar, Generic

from binance_f import RequestClient
from binance_f.model import Position, AccountInformation, Order
from market.Symbol import Symbol
from rest import post_stop_take_order, get_recent_trades_list
from rest.position.stop import position_stop_utils
from rest.position.stop.dto import StopResult
from rest.position.stop.position_stop_utils import StopState
from utils import position_utils
from utils.order_utils import OrdersInfo
from utils.position_utils import PositionFilter, filter_position


class StopDto(metaclass=ABCMeta):

    def __init__(self, symbol: str, positionSide: str, tags: List[str]):
        self.symbol: str = symbol
        self.positionSide: str = positionSide
        self.tags: List[str] = tags

    def get_symbol(self) -> Symbol:
        return Symbol.get(self.symbol)


T = TypeVar('T', bound=StopDto)


class Stoper(Generic[T], metaclass=ABCMeta):

    def __init__(self, client: RequestClient, state: StopState, dto: T):
        self.client = client
        self.dto: T = dto
        self.state: StopState = state
        self.position: Position = self.get_current_position()
        self.no_position = position_utils.get_abs_amt(self.position) <= 0
        self.tags = self._setup_tags(dto.tags)
        if self.no_position:
            return
        self.currentStopOrdersInfo: OrdersInfo = None
        self.lastPrice: float = None

    def load_vars(self):
        if self.no_position:
            raise TypeError('no position')
        self.currentStopOrdersInfo = position_stop_utils.get_current_new_stop_orders(
            self.client,
            self.position)
        self.lastPrice: float = get_recent_trades_list.get_last_price(self.client, self.dto.get_symbol())

    def _setup_tags(self, tags: List[str]) -> List[str]:
        tags.append(self.state.value)
        return tags

    def get_current_position(self) -> Position:
        result: List[Position] = self.client.get_position()
        pf = PositionFilter(symbol=self.dto.symbol, positionSide=self.dto.positionSide)
        result = filter_position(result, pf)
        return result[0]

    def get_account(self) -> AccountInformation:
        return self.client.get_account_information()

    def is_conformable(self) -> bool:
        """
        表示有達到該 range 的進入門檻
        """
        return not self.no_position

    @abc.abstractmethod
    def is_up_to_date(self) -> bool:
        return NotImplemented

    @abc.abstractmethod
    def clean_old_orders(self) -> List[Order]:
        return NotImplemented

    @abc.abstractmethod
    def stop(self) -> StopResult:
        return NotImplemented

    def run(self) -> StopResult:
        if self.no_position:
            return StopResult(stopState=self.state,noActiveMsg='no_position')
        if not self.is_conformable():
            return StopResult(stopState=self.state,noActiveMsg='not is_conformable')
        if self.is_up_to_date():
            return StopResult(stopState=self.state,active=True, up_to_date=True)
        self.clean_old_orders()
        return self.stop()
