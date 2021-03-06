from typing import List

from binance_f import RequestClient
from binance_f.model import OrderSide, OrderType, TimeInForce, WorkingType, PositionSide, Order
from market.Symbol import Symbol
from rest import get_recent_trades_list
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils
from utils.comm_utils import fix_precision


class Dto:

    def __init__(self, symbol: str, stopSide: str, stopPrice: float, quantity: float, tags: List[str] = list()):
        self.symbol: str = symbol
        self.stopSide: str = stopSide
        self.stopPrice: float = stopPrice
        self.quantity: float = quantity
        self.tags: List[str] = tags

    def get_symbol(self) -> Symbol:
        return Symbol.get(self.symbol)


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    pl = Dto(**payload)
    return post_stop_take_order(client=client, tags=pl.tags, stop_side=pl.stopSide, symbol=pl.get_symbol(),
                                stopPrice=pl.stopPrice, quantity=pl.quantity).__dict__


def post_stop_take_order(client: RequestClient, tags: List[str], stop_side: str,
                         symbol: Symbol, stopPrice: float,
                         quantity: float, lastPrice: float = None) -> Order:
    positionSide = PositionSide.SHORT if stop_side == OrderSide.BUY else PositionSide.LONG
    lastPrice = get_recent_trades_list.get_last_price(client, symbol) if lastPrice is None else lastPrice
    ordertype = _get_ordertype(orderSide=stop_side, lastPrice=lastPrice, stopPrice=stopPrice)
    stopPrice = fix_precision(symbol.precision_price, stopPrice)
    quantity = fix_precision(symbol.precision_amount, quantity)
    result = client.post_order(
        side=stop_side,
        symbol=f'{symbol.symbol}USDT',
        timeInForce=TimeInForce.GTC,
        ordertype=ordertype,
        workingType=WorkingType.CONTRACT_PRICE,
        positionSide=positionSide,
        stopPrice=stopPrice,
        quantity=quantity,
        newClientOrderId=comm_utils.get_order_cid(tags)
    )
    return result


def _get_ordertype(orderSide: str, lastPrice: float, stopPrice: float) -> OrderType:
    if orderSide == OrderSide.BUY:
        return OrderType.STOP_MARKET if lastPrice > stopPrice else OrderType.TAKE_PROFIT_MARKET
    else:
        return OrderType.STOP_MARKET if lastPrice < stopPrice else OrderType.TAKE_PROFIT_MARKET
