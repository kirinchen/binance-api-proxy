from typing import List

from binance_f import RequestClient
from binance_f.model import OrderSide, PositionSide, Order, TimeInForce, OrderType, WorkingType
from rest import get_recent_trades_list
from rest.order.dto import TakeProfitDto
from rest.order.order_builder import BaseOrderBuilder, PriceQty
from utils import position_utils, comm_utils


class TakeProfitOrderBuilder(BaseOrderBuilder[TakeProfitDto]):

    def __init__(self, client: RequestClient, dto: TakeProfitDto):
        super(TakeProfitOrderBuilder, self).__init__(client, dto)

    def get_order_side(self) -> str:
        return OrderSide.BUY if self.positionSide == PositionSide.SHORT else OrderSide.SELL

    def gen_price_qty_list(self) -> List[PriceQty]:
        lastPrice = get_recent_trades_list.get_last_rise_price(client=self.client, symbol=self.get_symbol(),
                                                               positionSide=self.positionSide,
                                                               buffRate=self.dto.priceBuffRate)
        all_qty: float = position_utils.get_abs_amt(self.position)
        part_qty: float = all_qty * self.dto.positionRate
        per_qty: float = part_qty / self.dto.size
        priceQtyList: List[PriceQty] = list
        for i in range(int(self.dto.size)):
            p = lastPrice * (1 + self.dto.gapRate)
            priceQtyList.append(PriceQty(
                price=p,
                quantity=per_qty
            ))
        return priceQtyList

    def post_one(self, pq: PriceQty) -> Order:
        price_str = str(self.get_symbol().fix_precision_price(pq.price))
        p_amt: float = self.get_symbol().fix_precision_amt(pq.quantity)
        if p_amt == 0:
            return None
        quantity_str = str(p_amt)
        result = self.client.post_order(
            side=self.get_order_side(),
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
