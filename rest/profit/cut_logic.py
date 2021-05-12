from abc import ABCMeta, abstractmethod
from typing import List

from binance_f import RequestClient
from binance_f.model import OrderSide, PositionSide, Order
from infr.constant import MAKER_FEE, TAKER_FEE
from rest import post_order, cancel_order
from rest.profit.profit_cuter import ProfitCuter

from utils import order_utils


class CutLogic(metaclass=ABCMeta):

    def __init__(self, cd: ProfitCuter):
        self.cutOrder = cd
        self.markPrice = self.cutOrder.position.markPrice
        self.entryPrice = self.cutOrder.position.entryPrice
        self.profitRate = self.calc_profit_rate()
        self.stepQuantity: float = (self.cutOrder.position.positionAmt * 1.00086) / self.cutOrder.payload.cutCount

    def setup_current_orders(self):
        self.currentOds: List[Order] = self.cutOrder.stopOrders
        self.sort_soon_orders()

    def get_maker_fee(self):
        return self.cutOrder.position.positionAmt * self.entryPrice * MAKER_FEE

    def get_taker_fee(self):
        return self.cutOrder.position.positionAmt * self.markPrice * TAKER_FEE

    def calc_current_soon_stop_price(self):
        return self.currentOds[0].stopPrice

    def is_rebuild_stop_orders(self) -> bool:

        if self.profitRate < self.cutOrder.payload.profitRate:
            return False
        if len(self.currentOds) <= 0:
            return True
        current_stop_sum_amt = order_utils.sum_amt(self.cutOrder.stopOrders)
        if current_stop_sum_amt < self.cutOrder.position.positionAmt:
            return True
        if self.check_over_soon_order():
            return True

        return False

    def cut(self, client: RequestClient):
        if not self.is_rebuild_stop_orders():
            return
        for sp in self.calc_step_prices():
            nods = post_order.post_stop_order(client=client, symbol=self.cutOrder.symbol,
                                              stop_side=self.get_stop_side(),
                                              stopPrice=sp,
                                              tags=['stop'],
                                              quantity=self.stepQuantity)

        result = client.cancel_list_orders(symbol=self.cutOrder.symbol.gen_with_usdt(),
                                           orderIdList=[od.orderId for od in self.currentOds])

    def clean_over_order(self, client: RequestClient):
        self.cutOrder.stopOrders.sort(key=lambda s: s.stopPrice, reverse=True)
        sumQ = 0.0
        for ods in self.cutOrder.stopOrders:
            if sumQ >= self.cutOrder.position.positionAmt:
                cancel_order.cancel_order(client, self.cutOrder.symbol, ods.orderId)
                continue
            sumQ += ods.origQty

    @abstractmethod
    def check_over_soon_order(self):
        pass

    @abstractmethod
    def sort_soon_orders(self):
        pass

    @abstractmethod
    def get_stop_side(self) -> str:
        pass

    def calc_profit_rate(self) -> float:
        spread = self.get_spread()
        fee = self.get_maker_fee() + self.get_taker_fee()
        pprofit = spread * self.cutOrder.position.positionAmt
        profit = pprofit - fee
        cost = (self.cutOrder.position.positionAmt * self.entryPrice) / self.cutOrder.position.leverage
        return profit / cost

    @abstractmethod
    def get_spread(self) -> float:
        pass

    @abstractmethod
    def calc_step_prices(self, cutCount: int, topRate: float) -> List[float]:
        pass


class LongCutLogic(CutLogic):

    def __init__(self, cd: ProfitCuter):
        super().__init__(cd)

    def check_over_soon_order(self):
        new_soon_price = self.calc_step_prices()[0]
        old_soon_price = self.currentOds[0].stopPrice
        return new_soon_price > old_soon_price

    def sort_soon_orders(self):
        self.currentOds.sort(key=lambda s: -s.stopPrice)

    def get_spread(self) -> float:
        return self.markPrice - self.entryPrice

    def get_stop_side(self) -> str:
        return OrderSide.SELL

    def calc_step_prices(self) -> List[float]:
        ans: List[float] = list()
        dp = (self.markPrice - self.entryPrice) * self.cutOrder.payload.topRate
        dsp = dp / self.cutOrder.payload.cutCount
        for i in range(self.cutOrder.payload.cutCount):
            p = (dsp * (i + 1)) + self.entryPrice
            ans.append(p)
        ans.reverse()
        return ans


class ShortCutLogic(CutLogic):

    def sort_soon_orders(self):
        self.currentOds.sort(key=lambda s: s.stopPrice)

    def __init__(self, cd: ProfitCuter):
        super().__init__(cd)

    def check_over_soon_order(self):
        new_soon_price = self.calc_step_prices()[0]
        old_soon_price = self.currentOds[0].stopPrice
        return new_soon_price < old_soon_price

    def get_spread(self) -> float:
        return self.entryPrice - self.markPrice

    def calc_step_prices(self) -> List[float]:
        ans: List[float] = list()
        dp = (self.entryPrice - self.markPrice) * self.cutOrder.payload.topRate
        dsp = dp / self.cutOrder.payload.cutCount
        for i in range(self.cutOrder.payload.cutCount):
            p = (dsp * (i + 1)) + self.markPrice
            ans.append(p)
        ans.reverse()
        return ans

    def get_stop_side(self) -> str:
        return OrderSide.BUY
