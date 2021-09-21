import abc
from abc import ABCMeta
from typing import List, TypeVar, Generic

from binance_f import RequestClient
from binance_f.model import Position, AccountInformation
from market.Symbol import Symbol
from rest.position.stop import position_stop_utils
from rest.position.stop.dto import StopResult
from rest.position.stop.position_stop_utils import StopState
from utils import position_utils
from utils.order_utils import SubtotalBundle
from utils.position_utils import PositionFilter, filter_position


class StopDto(metaclass=ABCMeta):

    def __init__(self, symbol: str, positionSide: str,tags: List[str]):
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
        (self.currentStopOrdersInfo, self.currentStopOdAvgPrice) = position_stop_utils.get_current_new_stop_orders(
            self.client,
            self.position)
        self.currentStopOrdersInfo: SubtotalBundle = self.currentStopOrdersInfo

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

    @abc.abstractmethod
    def stop(self) -> StopResult:
        return NotImplemented
