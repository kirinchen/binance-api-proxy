from typing import List

from binance_f import RequestClient
from binance_f.model import Order, AccountInformation, Position, OrderSide, PositionSide, TimeInForce, OrderType, \
    WorkingType
from market.Symbol import Symbol
from rest import get_recent_trades_list
from rest.poxy_controller import PayloadReqKey
from utils import position_utils, comm_utils
from utils.position_utils import PositionFilter


class PriceQty:

    def __init__(self, price: float, quantity: float):
        self.price: float = price
        self.quantity: float = quantity


class OrderBuilder:

    def __init__(self, client: RequestClient, symbol: str, positionSide: str, tags: List[str] = list(), **kwargs):
        self.client: RequestClient = client
        self.symbol: str = symbol
        self.positionSide: str = positionSide
        self.tags: List[str] = list(tags)
        self.position: Position = self.get_current_position()
        self.orderSide: str = self._get_order_side()
        self.priceQtyList: List[PriceQty] = list()

    def get_symbol(self) -> Symbol:
        return Symbol.get(self.symbol)

    def _get_order_side(self) -> str:
        return OrderSide.BUY if self.positionSide == PositionSide.SHORT else OrderSide.SELL

    def get_current_position(self) -> Position:
        result: List[Position] = self.client.get_position()
        pf = PositionFilter(symbol=self.symbol, positionSide=self.positionSide)
        result = position_utils.filter_position(result, pf)
        return result[0]

    def init_price_qty_list(self, positionRate: float, priceBuffRate: float, size: int, gapRate: float, **kwargs):
        lastPrice = get_recent_trades_list.get_last_rise_price(client=self.client, symbol=self.get_symbol(),
                                                               positionSide=self.positionSide,
                                                               buffRate=priceBuffRate)
        all_qty: float = position_utils.get_abs_amt(self.position)
        part_qty: float = all_qty * positionRate
        per_qty: float = part_qty / size
        self.priceQtyList.clear()
        for i in range(int(size)):
            p = lastPrice * (1 + gapRate)
            self.priceQtyList.append(PriceQty(
                price=p,
                quantity=per_qty
            ))

    def post(self) -> List[Order]:
        ans: List[Order] = list()
        for pq in self.priceQtyList:
            ans.append(self.post_one(pq))
        return ans

    def post_one(self, pq: PriceQty) -> Order:
        price_str = str(self.get_symbol().fix_precision_price(pq.price))
        quantity_str = str(self.get_symbol().fix_precision_amt(pq.quantity))
        result = self.client.post_order(
            side=self.orderSide,
            symbol=self.get_symbol().gen_with_usdt(),
            timeInForce=TimeInForce.GTC,
            ordertype=OrderType.TAKE_PROFIT_MARKET,
            workingType=WorkingType.CONTRACT_PRICE,
            positionSide=self.positionSide,
            stopPrice=price_str,
            quantity=quantity_str,
            newClientOrderId=comm_utils.get_order_cid(self.tags)
        )
        return result


def run(client: RequestClient, payload: dict):
    try:
        PayloadReqKey.clean_default_keys(payload)
        ob = OrderBuilder(client=client, **payload)
        ob.init_price_qty_list(**payload)
        return comm_utils.to_dict(ob.post())
    except Exception as e:  # work on python 3.x
        return str(e)
