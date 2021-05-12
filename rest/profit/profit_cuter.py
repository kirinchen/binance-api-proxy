from typing import List

from binance_f import RequestClient
from binance_f.model import Position, Order, OrderType
from market.Symbol import Symbol
from rest import profit


from rest.profit.dto import CutProfitDto
from utils.order_utils import filter_order, OrderFilter


class ProfitCuter:

    def __init__(self, pos: Position, symbol: Symbol, orders: List[Order], payload: CutProfitDto):

        self.position = pos
        self.payload = payload
        self.symbol = symbol
        self.logic = profit.gen_cut_logic(self)
        self.stopOrders: List[Order] = filter_order(orders, OrderFilter(
            symbol=self.symbol.symbol,
            side=self.logic.get_stop_side(),
            orderType=OrderType.STOP_MARKET
        )).orders
        self.logic.setup_current_orders()


    def cut(self, client: RequestClient):
        if self.position and self.logic:
            self.logic.cut(client)
