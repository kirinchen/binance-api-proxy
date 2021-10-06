from typing import List

from binance_f import RequestClient
from binance_f.model import OrderSide, PositionSide, Order, TimeInForce, OrderType, WorkingType
from rest import get_recent_trades_list
from rest.order.dto import TakeProfitDto
from rest.order.order_builder import BaseOrderBuilder, PriceQty, LoadDataCheck
from utils import position_utils, comm_utils


class TakeProfitOrderBuilder(BaseOrderBuilder[TakeProfitDto]):

    def __init__(self, client: RequestClient, dto: TakeProfitDto):
        super(TakeProfitOrderBuilder, self).__init__(client, dto)
        self.position_quantity: float = None

    def load_data(self) -> LoadDataCheck:
        self.position_quantity: float = position_utils.get_abs_amt(self.get_current_position())
        if self.position_quantity <= 0:
            return LoadDataCheck(success=False, failsMsg='no has position amt')
        return LoadDataCheck(success=True)

    def get_order_side(self) -> str:
        return OrderSide.BUY if self.dto.positionSide == PositionSide.SHORT else OrderSide.SELL

    def gen_price_qty_list(self) -> List[PriceQty]:
        lastPrice = get_recent_trades_list.get_last_rise_price(client=self.client, symbol=self.dto.get_symbol(),
                                                               positionSide=self.dto.positionSide,
                                                               buffRate=self.dto.priceBuffRate)
        part_qty: float = self.position_quantity * self.dto.positionRate
        per_qty: float = comm_utils.calc_proportional_first(sum=part_qty, rate=self.dto.proportionalRate,
                                                            n=self.dto.size)
        priceQtyList: List[PriceQty] = list()
        for i in range(int(self.dto.size)):
            p = lastPrice * (1 + self.dto.gapRate)
            q = per_qty * pow(self.dto.proportionalRate, i)
            priceQtyList.append(PriceQty(
                price=p,
                quantity=q
            ))
        return priceQtyList

    def post_one(self, pq: PriceQty) -> Order:
        price_str = str(self.dto.get_symbol().fix_precision_price(pq.price))
        p_amt: float = self.dto.get_symbol().fix_precision_amt(pq.quantity)
        if p_amt == 0:
            return None
        quantity_str = str(p_amt)
        result = self.client.post_order(
            side=self.get_order_side(),
            symbol=self.dto.get_symbol().gen_with_usdt(),
            timeInForce=TimeInForce.GTC,
            ordertype=OrderType.TAKE_PROFIT_MARKET,
            workingType=WorkingType.CONTRACT_PRICE,
            positionSide=self.dto.positionSide,
            stopPrice=price_str,
            quantity=quantity_str,
            newClientOrderId=comm_utils.get_order_cid(self.dto.tags)
        )
        return result
