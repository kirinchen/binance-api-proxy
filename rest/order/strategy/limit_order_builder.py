from typing import List

from binance_f import RequestClient
from binance_f.model import Order
from rest import get_recent_trades_list
from rest.order.dto import LimitDto
from rest.order.order_builder import BaseOrderBuilder, PriceQty
from utils import direction_utils


class TakeProfitOrderBuilder(BaseOrderBuilder[LimitDto]):

    def __init__(self, client: RequestClient, dto: LimitDto):
        super(TakeProfitOrderBuilder, self).__init__(client, dto)

    def get_order_side(self) -> str:
        return direction_utils.get_limit_order_side(self.dto. positionSide)

    def gen_price_qty_list(self) -> List[PriceQty]:
        ans: List[Order] = list()
        per_withdrawAmountRate = self.dto. withdrawAmountRate / self.dto. size
        lastPrice = get_recent_trades_list.get_last_fall_price(client=client, symbol=symbol,
                                                               positionSide=positionSide)
        p = _opt_price(client=client, positionSide=positionSide, symbol=Symbol.get(symbol), price=price)
        for i in range(int(size)):
            r: float = 1 + (gapRate * i)
            per_price = direction_utils.fall_price(positionSide=positionSide, orgPrice=p, rate=r)
            ans.append(post_limit_order(client=client, positionSide=positionSide, symbol=symbol, tags=tags,
                                        withdrawAmountRate=per_withdrawAmountRate, price=per_price))
        return ans

    def post_one(self, pq: PriceQty) -> Order:
        pass
