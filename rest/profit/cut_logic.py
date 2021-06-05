from abc import ABCMeta, abstractmethod
from typing import List

from binance_f import RequestClient
from binance_f.model import OrderSide, PositionSide, Order
from infr.constant import MAKER_FEE, TAKER_FEE
from rest import post_order, cancel_order
from rest.profit.profit_cuter import ProfitCuter
from rest.stop_loss import LossStoper

from utils import order_utils, position_utils


class CutLogic(metaclass=ABCMeta):

    def __init__(self, cd: ProfitCuter):
        self.cutOrder = cd
        self.markPrice = self.cutOrder.position.markPrice
        self.entryPrice = self.cutOrder.position.entryPrice
        self.profitRate = self.calc_profit_rate()
        self.stepQuantity: float = self.calc_step_quantity()

    def setup_current_orders(self):
        self.currentOds: List[Order] = self.cutOrder.stopOrders
        self.sort_soon_orders()

    def get_maker_fee(self):
        return self.get_pos_amt() * self.entryPrice * MAKER_FEE

    def get_taker_fee(self):
        return self.get_pos_amt() * self.markPrice * TAKER_FEE

    def calc_current_soon_stop_price(self):
        return self.currentOds[0].stopPrice

    def is_rebuild_stop_orders(self) -> bool:

        if self.profitRate < self.cutOrder.payload.profitRate:
            return False
        if len(self.currentOds) <= 0:
            return True
        current_stop_sum_amt = order_utils.sum_amt(self.cutOrder.stopOrders)
        if current_stop_sum_amt < self.get_pos_amt():
            return True
        if self.check_over_soon_order():
            return True

        return False

    def get_pos_amt(self):
        return position_utils.get_abs_amt(self.cutOrder.position)

    def cut(self, client: RequestClient):
        if not self.is_rebuild_stop_orders():
            self._stop_loss(client)
            return
        self.clean_old_order(client)
        for sp in self.calc_step_prices():
            nods = post_order.post_stop_order(client=client, symbol=self.cutOrder.symbol,
                                              stop_side=self.get_stop_side(),
                                              stopPrice=sp,
                                              tags=['stop'],
                                              quantity=self.stepQuantity)
        self._stop_loss(client)

    def clean_old_order(self, client: RequestClient):
        try:
            if self.currentOds and len(self.currentOds) > 0:
                result = client.cancel_list_orders(symbol=self.cutOrder.symbol.gen_with_usdt(),
                                                   orderIdList=[od.orderId for od in self.currentOds])
        except Exception as e:  # work on python 3.x
            print('Failed to upload to ftp: ' + str(e))

    def _stop_loss(self, client: RequestClient):
        ls = LossStoper(client=client, position=self.cutOrder.position, stopRate=0.00688)
        ls.stop()

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
        pprofit = spread * self.get_pos_amt()
        profit = pprofit - fee
        cost = (self.get_pos_amt() * self.entryPrice) / self.cutOrder.position.leverage
        return profit / cost

    @abstractmethod
    def get_spread(self) -> float:
        pass

    @abstractmethod
    def calc_step_prices(self, cutCount: int, topRate: float) -> List[float]:
        pass

    @abstractmethod
    def calc_step_quantity(self) -> float:
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
        dto = self.cutOrder.payload
        ans: List[float] = list()
        bottomPrice = self.entryPrice * (1 + dto.bottomRate)
        dp = (self.markPrice - bottomPrice) * dto.topRate
        dsp = dp / self.cutOrder.payload.cutCount
        for i in range(self.cutOrder.payload.cutCount):
            pp = (dsp * (i + 1))
            ppr = pp / bottomPrice
            if ppr >= dto.minStepRate:
                ans.append(pp + bottomPrice)
        ans.reverse()
        return ans

    def calc_step_quantity(self) -> float:
        return position_utils.get_abs_amt(self.cutOrder.position) * 1.001168 / self.cutOrder.payload.cutCount


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
        dto = self.cutOrder.payload
        ans: List[float] = list()
        bottomPrice = self.entryPrice * (1 + dto.bottomRate)
        dp = (bottomPrice - self.markPrice) * self.cutOrder.payload.topRate
        dsp = dp / self.cutOrder.payload.cutCount
        for i in range(self.cutOrder.payload.cutCount):
            pp = (dsp * (i + 1))
            ppr = pp / bottomPrice
            if ppr >= dto.minStepRate:
                ans.append( bottomPrice - pp)
        ans.reverse()
        return ans

    def get_stop_side(self) -> str:
        return OrderSide.BUY

    def calc_step_quantity(self) -> float:
        return position_utils.get_abs_amt(self.cutOrder.position) * 1.001168 / self.cutOrder.payload.cutCount


