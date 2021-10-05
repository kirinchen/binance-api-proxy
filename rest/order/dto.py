from enum import Enum
from typing import List

from market.Symbol import Symbol
from utils import comm_utils


class OrderStrategy(Enum):
    TAKE_PROFIT = 'TAKE_PROFIT'
    LIMIT = 'LIMIT'


class BaseDto:

    def __init__(self, symbol: str, positionSide: str, strategy: str, priceBuffRate: float, gapRate: float,
                 size: int = 1,
                 proportionalRate: float = 1,
                 tags: List[str] = list(), **kwargs):
        self.strategy: str = strategy
        self.symbol: str = symbol
        self.positionSide: str = positionSide
        self.priceBuffRate: float = priceBuffRate
        self.gapRate: float = gapRate
        self.proportionalRate: float = proportionalRate
        self.size: int = size
        self.tags: List[str] = list(tags)

    def get_symbol(self) -> Symbol:
        return Symbol.get(self.symbol)

    def get_strategy(self) -> OrderStrategy:
        return comm_utils.value_of_enum(OrderStrategy, self.strategy)


class TakeProfitDto(BaseDto):

    def __init__(self, positionRate: float, **kwargs):
        super(TakeProfitDto, self).__init__(**kwargs)
        self.positionRate: float = positionRate


class LimitDto(BaseDto):

    def __init__(self, withdrawAmountRate: float, **kwargs):
        super(LimitDto, self).__init__(**kwargs)
        self.withdrawAmountRate: float = withdrawAmountRate
