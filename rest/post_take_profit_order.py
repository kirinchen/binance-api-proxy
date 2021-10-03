from typing import List

from binance_f import RequestClient
from binance_f.model import Order, AccountInformation, Position
from market.Symbol import Symbol
from rest import get_recent_trades_list
from utils import position_utils
from utils.position_utils import PositionFilter


class BaseDto:

    def __init__(self, symbol: str, positionSide: str, positionRate: float, priceBuffRate: float = 0,
                 tags: List[str] = list()
                 ):
        self.symbol: str = symbol
        self.positionSide: str = positionSide
        self.positionRate: float = positionRate
        self.tags: List[str] = tags
        self.priceBuffRate: float = priceBuffRate

    def get_symbol(self) -> Symbol:
        return Symbol.get(self.symbol)


class PriceQty:

    def __init__(self, price: float, quantity: float):
        self.price: float = price
        self.quantity: float = quantity


class OrderBuilder:

    def __init__(self, client: RequestClient, symbol: str, positionSide: str, tags: List[str] = list()):
        self.client: RequestClient = client
        self.symbol: str = symbol
        self.positionSide: str = positionSide
        self.tags: List[str] = list(tags)
        self.position:Position = self.get_current_position()
        self.priceQtyList: List[PriceQty] = list()

    def get_current_position(self) -> Position:
        result: List[Position] = self.client.get_position()
        pf = PositionFilter(symbol=self.symbol, positionSide=self.positionSide)
        result = position_utils.filter_position(result, pf)
        return result[0]

    def init_price_qty_list(self, positionRate: float, priceBuffRate: float, size: int):
        lastPrice = get_recent_trades_list.get_last_safe_limit_price(client=self.client, symbol=self.symbol,
                                                                     positionSide=self.positionSide,
                                                                     buffRate=priceBuffRate)
        all_qty :float  = position_utils.get_abs_amt(self.position)


def post_take_profit_order(client: RequestClient, dto: BaseDto) -> Order:
    symbol: Symbol = dto.get_symbol()
    account: AccountInformation = client.get_account_information()
