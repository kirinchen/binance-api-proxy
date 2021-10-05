from enum import Enum
from typing import List

from market.Symbol import Symbol
from utils import comm_utils


class OrderStrategy(Enum):
    TAKE_PROFIT = 'TAKE_PROFIT'


class BaseDto:

    def __init__(self, symbol: str, positionSide: str, strategy: str, tags: List[str] = list(), **kwargs):
        self.strategy: str = strategy
        self.symbol: str = symbol
        self.positionSide: str = positionSide
        self.tags: List[str] = list(tags)

    def get_symbol(self) -> Symbol:
        return Symbol.get(self.symbol)

    def get_strategy(self) -> OrderStrategy:
        return comm_utils.value_of_enum(OrderStrategy, self.strategy)


class TakeProfitDto(BaseDto):

    def __init__(self, positionRate: float, priceBuffRate: float, size: int, gapRate: float, **kwargs):
        super(TakeProfitDto, self).__init__(**kwargs)
        self.positionRate: float = positionRate
        self.priceBuffRate: float = priceBuffRate
        self.gapRate: float = gapRate
        self.size: int = size


class LimitDto(BaseDto):

    def __init__(self, withdrawAmountRate: float, priceBuffRate: float, size: int, gapRate: float, **kwargs):
        super(LimitDto, self).__init__(**kwargs)
        self.withdrawAmountRate: float = withdrawAmountRate
        self.priceBuffRate: float = priceBuffRate
        self.gapRate: float = gapRate
        self.size: int = size
