from random import random

from binance_f import RequestClient
from binance_f.model import Position, PositionSide, Order, TimeInForce, WorkingType, OrderRespType, OrderType, OrderSide
from market.Symbol import Symbol
from rest.profit import ProfitCuter
from rest.profit.dto import CutProfitDto


class FClient(RequestClient):

    def post_order(self, symbol: 'str', side: 'OrderSide', ordertype: 'OrderType',
                   timeInForce: 'TimeInForce' = TimeInForce.INVALID, quantity: 'float' = None,
                   reduceOnly: 'boolean' = None, price: 'float' = None,
                   newClientOrderId: 'str' = None, stopPrice: 'float' = None,
                   workingType: 'WorkingType' = WorkingType.INVALID, closePosition: 'boolean' = None,
                   positionSide: 'PositionSide' = PositionSide.INVALID, callbackRate: 'float' = None,
                   activationPrice: 'float' = None, newOrderRespType: 'OrderRespType' = OrderRespType.INVALID) -> any:
        print('stopPrice=' + stopPrice)

    def cancel_list_orders(self, symbol: 'str', orderIdList: 'list' = None,
                           origClientOrderIdList: 'list' = None) -> any:
        print('cancel_list_orders:' + str(orderIdList))


rc = FClient()

symbol = Symbol.ETH


def gen_payload(positionSide: str) -> CutProfitDto:
    return CutProfitDto(symbol=symbol.symbol, profitRate=0.7, topRate=0.85, cutCount=3, positionSide=positionSide)


def gen_pos(positionSide: str) -> Position:
    pos = Position()
    pos.symbol = symbol.gen_with_usdt()
    pos.positionSide = positionSide
    pos.positionAmt = 10
    pos.leverage = 100
    pos.markPrice = 5000 if positionSide == PositionSide.LONG else 3000
    pos.entryPrice = 3000 if positionSide == PositionSide.LONG else 5000
    return pos


def gen_order(stopPrice: float, origQty: float, side: str) -> Order:
    ans = Order()
    ans.symbol = symbol.gen_with_usdt()
    ans.orderId = '111'
    ans.stopPrice = stopPrice
    ans.origQty = origQty
    ans.type = OrderType.STOP_MARKET
    ans.positionSide = PositionSide.LONG
    ans.side = side
    return ans


def test_buy_new():
    ps = PositionSide.LONG
    pc = ProfitCuter(pos=gen_pos(ps), symbol=symbol, orders=[gen_order(2000, 10, OrderSide.SELL)],
                     payload=gen_payload(ps))
    pc.cut(client=rc)


def test_sell_new():
    ps = PositionSide.SHORT
    pc = ProfitCuter(pos=gen_pos(ps), symbol=symbol, orders=[gen_order(6000, 10, OrderSide.BUY)],
                     payload=gen_payload(ps))
    pc.cut(client=rc)