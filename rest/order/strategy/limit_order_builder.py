from typing import List

from binance_f import RequestClient
from binance_f.model import Order, AccountInformation, Position, TimeInForce, OrderType, WorkingType
from rest import get_recent_trades_list
from rest.order.dto import LimitDto
from rest.order.order_builder import BaseOrderBuilder, PriceQty, LoadDataCheck
from utils import direction_utils, comm_utils


class LimitOrderBuilder(BaseOrderBuilder[LimitDto]):

    def __init__(self, client: RequestClient, dto: LimitDto):
        super(LimitOrderBuilder, self).__init__(client, dto)
        self.account: AccountInformation = None
        self.position: Position = None
        self.account: AccountInformation = None
        self.amount: float = None
        self.lastPrice: float = None

    def load_data(self) -> LoadDataCheck:
        self.position = self.get_current_position()
        self.account = self.client.get_account_information()
        self.amount = self.account.maxWithdrawAmount * self.dto.withdrawAmountRate
        self.lastPrice = get_recent_trades_list.get_last_fall_price(client=self.client, symbol=self.dto.get_symbol(),
                                                                    positionSide=self.dto.positionSide,
                                                                    buffRate=self.dto.priceBuffRate)
        minUsdAmt: float = self.dto.get_symbol().get_min_usd_amount(self.lastPrice)
        leverage_amt: float = self.amount * self.position.leverage
        if minUsdAmt > leverage_amt:
            return LoadDataCheck(success=False, failsMsg=f'not have enough {minUsdAmt} > {leverage_amt}')
        return LoadDataCheck(success=True)

    def get_order_side(self) -> str:
        return direction_utils.get_limit_order_side(self.dto.positionSide)

    def _calc_quantity(self, quote: float, amount: float) -> float:
        max_ratio = self.position.maxNotionalValue / amount
        ratio = min(max_ratio, self.position.leverage)
        quantity = (amount * ratio) / quote
        return quantity

    def gen_price_qty_list(self) -> List[PriceQty]:

        base_amt: float = comm_utils.calc_proportional_first(sum=self.amount, rate=self.dto.proportionalRate,
                                                             n=self.dto.size)

        priceQtyList: List[PriceQty] = list()
        for i in range(int(self.dto.size)):
            p = self.lastPrice * pow(1 + self.dto.gapRate, i)
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
