from typing import List

from binance_f import RequestClient
from binance_f.model import Order, AccountInformation, Position, TimeInForce, OrderType, WorkingType
from rest import get_recent_trades_list
from rest.order.dto import LimitDto
from rest.order.order_builder import BaseOrderBuilder, PriceQty
from utils import direction_utils, comm_utils


class LimitOrderBuilder(BaseOrderBuilder[LimitDto]):

    def __init__(self, client: RequestClient, dto: LimitDto):
        super(LimitOrderBuilder, self).__init__(client, dto)

        self.position: Position = self.get_current_position()

    def get_order_side(self) -> str:
        return direction_utils.get_limit_order_side(self.dto.positionSide)

    def _calc_quantity(self, quote: float, amount: float) -> float:
        max_ratio = self.position.maxNotionalValue / amount
        ratio = min(max_ratio, self.position.leverage)
        quantity = (amount * ratio) / quote
        return quantity

    def gen_price_qty_list(self) -> List[PriceQty]:

        account: AccountInformation = self.client.get_account_information()
        amount = account.maxWithdrawAmount * self.dto.withdrawAmountRate

        base_amt: float = comm_utils.calc_proportional_first(sum=amount, rate=self.dto.proportionalRate,
                                                             n=self.dto.size)
        lastPrice = get_recent_trades_list.get_last_fall_price(client=self.client, symbol=self.dto.get_symbol(),
                                                               positionSide=self.dto.positionSide,
                                                               buffRate=self.dto.priceBuffRate)

        priceQtyList: List[PriceQty] = list()
        for i in range(int(self.dto.size)):
            p = lastPrice * (1 + self.dto.gapRate)
            pre_amt: float = base_amt * pow(self.dto.proportionalRate, i)
            qty: float = self._calc_quantity(quote=p, amount=pre_amt)
            priceQtyList.append(PriceQty(
                price=p,
                quantity=qty
            ))
        return priceQtyList

    def post_one(self, pq: PriceQty) -> Order:
        price_str = str(self.dto.get_symbol().fix_precision_price(pq.price))

        p_amt: float = self.dto.get_symbol().fix_precision_amt(pq.quantity)
        if p_amt == 0:
            return None
        quantity_str = str(p_amt)

        return self.client.post_order(price=price_str,
                                      side=self.get_order_side(),
                                      symbol=self.dto.get_symbol().gen_with_usdt(),
                                      timeInForce=TimeInForce.GTC,
                                      ordertype=OrderType.LIMIT,
                                      workingType=WorkingType.CONTRACT_PRICE,
                                      positionSide=self.dto.positionSide,
                                      # activationPrice=None,
                                      # closePosition=False,
                                      quantity=quantity_str,
                                      newClientOrderId=comm_utils.get_order_cid(tags=self.dto.tags)
                                      )
