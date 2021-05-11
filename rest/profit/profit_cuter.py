from typing import List

from binance_f import RequestClient
from binance_f.model import Position, Order, OrderType
from market.Symbol import Symbol
from rest.profit.cut import CutProfitDto
from utils.order_utils import filter_order, OrderFilter


class ProfitCuter:

    def __init__(self, pos: Position, symbol: Symbol, orders: List[Order],payload: CutProfitDto):
        if pos.positionAmt <= 0:
            return
        self.position = pos
        self.payload = payload
        self.symbol = symbol
        self.logic = gen_cut_logic(self)
        self.stopOrders:List[Order] = filter_order(orders, OrderFilter(
            symbol=self.symbol.symbol,
            side=self.logic.get_stop_side(),
            orderType=OrderType.STOP_MARKET
        )).orders

    def cut(self, client: RequestClient ):
        if self.position and self.logic:
            self.logic.cut(client)
