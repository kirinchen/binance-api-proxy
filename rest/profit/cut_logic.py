from abc import ABCMeta, abstractmethod
from typing import List

from binance_f import RequestClient
from binance_f.model import OrderSide, PositionSide, Order
from infr.constant import MAKER_FEE, TAKER_FEE
from rest import post_order, cancel_order
from rest.profit.cut import CutProfitDto
from rest.profit.profit_cuter import ProfitCuter
from utils import order_utils


class AmtPrice:
    def __init__(self, amt: float, price: float, newed: bool = False):
        self.amt = amt
        self.price = price
        self.newed = newed


class ProfitEnoughException(Exception):
    pass


class CutLogic(metaclass=ABCMeta):

    def __init__(self, cd: ProfitCuter):
        self.cutOrder = cd
        self.markPrice = self.cutOrder.position.markPrice
        self.entryPrice = self.cutOrder.position.entryPrice
        self.currentOds: List[Order] = self.cutOrder.stopOrders
        self.profitRate = self.calc_profit_rate()
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

        return False

    def _calc_bundle(self, payload: CutProfitDto):
        self.profitRate = self.calc_profit_rate()
        if self.profitRate < payload.profitRate:
            raise ProfitEnoughException(str(self.profitRate) + '<' + str(payload.profitRate))
        self.stepQuantity = self.cutOrder.position.positionAmt / payload.cutCount
        sp = self.calc_step_prices(payload.cutCount, payload.topRate)
        self._add_step_prices(sp)

    # TODO stepQuantity move tp _add_step_prices

    def _add_step_prices(self, ps: List[float]):
        sumQ = 0.0
        aps = self._list_amt_price(ps)
        for p in aps:
            if sumQ > self.cutOrder.position.positionAmt:
                return
            if p.newed:
                self.stepPrices.append(p.price)
            sumQ += p.amt

    def _list_amt_price(self, ps: List[float]) -> List[AmtPrice]:
        ans: List[AmtPrice] = list()
        for p in ps:
            ans.append(AmtPrice(self.stepQuantity, p, True))
        for ods in self.cutOrder.stopOrders:
            ans.append(AmtPrice(ods.origQty, ods.stopPrice, False))
        self.sort_amt_price(ans)
        return ans

    def cut(self, client: RequestClient, payload: CutProfitDto):
        try:
            self._calc_bundle(payload)
        except ProfitEnoughException:
            print("not over th")
            return
        for sp in self.stepPrices:
            nods = post_order.post_stop_order(client=client, symbol=self.cutOrder.symbol,
                                              stop_side=self.get_stop_side(),
                                              stopPrice=sp,
                                              tags=['stop'],
                                              quantity=self.stepQuantity)
            self.cutOrder.stopOrders.append(nods)
        self.clean_over_order(client)

    def clean_over_order(self, client: RequestClient):
        self.cutOrder.stopOrders.sort(key=lambda s: s.stopPrice, reverse=True)
        sumQ = 0.0
        for ods in self.cutOrder.stopOrders:
            if sumQ >= self.cutOrder.position.positionAmt:
                cancel_order.cancel_order(client, self.cutOrder.symbol, ods.orderId)
                continue
            sumQ += ods.origQty


    def calc_new_soon_stop_price(self):
        steps = self.calc_step_prices()


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



    def sort_soon_orders(self):
        self.currentOds.sort(key=lambda s: -s.stopPrice)

    def get_spread(self) -> float:
        return self.markPrice - self.entryPrice

    def get_stop_side(self) -> str:
        return OrderSide.SELL

    def calc_step_prices(self, cutCount: int, topRate: float) -> List[float]:
        ans: List[float] = list()
        dp = (self.markPrice - self.entryPrice) * topRate
        dsp = dp / cutCount
        for i in range(cutCount):
            p = (dsp * (i + 1)) + self.entryPrice
            ans.append(p)
        return ans


class ShortCutLogic(CutLogic):

    def __init__(self, cd: ProfitCuter):
        super().__init__(cd)

    def get_spread(self) -> float:
        return self.entryPrice - self.markPrice

    def sort_amt_price(self, aps: List[AmtPrice]):
        aps.sort(key=lambda s: s.price, reverse=True)

    def calc_step_prices(self, cutCount: int, topRate: float) -> List[float]:
        ans: List[float] = list()
        dp = (self.entryPrice - self.markPrice) * topRate
        dsp = dp / cutCount
        for i in range(cutCount):
            p = (dsp * (i + 1)) + self.markPrice
            ans.append(p)
        return ans

    def get_stop_side(self) -> str:
        return OrderSide.BUY


def gen_cut_logic(cd: ProfitCuter) -> CutLogic:
    return {
        PositionSide.LONG: LongCutLogic(cd),
        PositionSide.SHORT: ShortCutLogic(cd)
    }.get(cd.position.positionSide)
