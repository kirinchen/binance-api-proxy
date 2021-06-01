from typing import List

from binance_f import RequestClient

from binance_f.model import Position, PositionSide, OrderSide, Order, OrderType
from market.Symbol import Symbol
from rest import post_order
from rest.poxy_controller import PayloadReqKey
from utils import order_utils
from utils.order_utils import OrderFilter, filter_order
from utils.position_utils import PositionFilter, filter_position


class LossStoper:

    def __init__(self, client: RequestClient, position: Position, stopRate: float, stopOrders: List[Order] = None):
        self.client = client
        self.position = position
        self.stopRate = stopRate
        self.stopOrders = stopOrders
        self.setup_stop_orders()
        self.stopAmt = order_utils.sum_amt(self.stopOrders)
        amt = self.position.positionAmt if self.position.positionSide == PositionSide.LONG else -self.position.positionAmt
        self.diffAmt = amt - self.stopAmt
        self.stopPrice = self.calc_stop_price()

    def setup_stop_orders(self):
        if self.stopOrders:
            return
        ods: List[Order] = self.client.get_open_orders(self.position.symbol)
        self.stopOrders: List[Order] = filter_order(ods, OrderFilter(
            symbol=Symbol.get_with_usdt( self.position.symbol).symbol,
            side=self.get_stop_side(),
            orderType=OrderType.STOP_MARKET
        )).orders

    def calc_stop_price(self) -> float:
        mkpc = self.position.markPrice
        dp = mkpc * self.stopRate
        dp = -dp if self.position.positionSide == PositionSide.LONG else dp
        return mkpc + dp

    def get_stop_side(self):
        return OrderSide.SELL if self.position.positionSide == PositionSide.LONG else OrderSide.BUY

    def stop(self):
        if self.diffAmt <= 0:
            return
        q = self.diffAmt / 3
        for i in range(3):
            post_order.post_stop_order(client=self.client, symbol=Symbol.get_with_usdt( self.position.symbol),
                                       stop_side=self.get_stop_side(),
                                       stopPrice=self.stopPrice,
                                       tags=['stop'],
                                       quantity=q)


class PayLoad:

    def __init__(self, symbol: str, positionSide: str, stopRate:float):
        self.symbol: Symbol = Symbol.get(symbol)
        self.positionSide = positionSide
        self.stopRate = stopRate


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    pl = PayLoad(**payload)
    result: List[Position] = client.get_position()
    pf = PositionFilter(symbol=pl.symbol.symbol, positionSide=pl.positionSide)
    p = filter_position(result, pf)[0]
    ls = LossStoper(client=client,position=p,stopRate=pl.stopRate)
    ls.stop()
    return {}
