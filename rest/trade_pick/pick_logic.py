from abc import ABCMeta, abstractmethod

from binance_f.model import OrderSide
from rest.trade_pick.trail_picker import TrailPickDto
from utils.trade_utils import TradeSet


class CheckedResult:

    def __init__(self, price: float, moreRate: float):
        self.price: float = price
        self.moreRate: float = moreRate


class PickLogic(metaclass=ABCMeta):

    def __init__(self, dto: TrailPickDto):
        self.dto: TrailPickDto = dto
        self.result: CheckedResult = None

    def on_check(self, ts: TradeSet) -> bool:
        camt = self.get_amt(ts)
        ccRate = self.calc_compared_rate(ts)
        print(f'amt:{camt} ccr:{ccRate}')
        if camt < self.dto.triggerAmt:
            return False
        if ccRate < self.dto.comparedRate:
            return False
        self.packResult(ts, camt)
        return True

    def packResult(self, ts: TradeSet, camt: float):
        ans = CheckedResult(price=self.get_last_price(ts), moreRate=camt / self.dto.triggerAmt)
        return ans

    @abstractmethod
    def get_amt(self, ts: TradeSet) -> float:
        pass

    @abstractmethod
    def calc_compared_rate(self, ts: TradeSet) -> float:
        pass

    @abstractmethod
    def get_last_price(self, ts: TradeSet) -> float:
        pass


class ToBuyLogic(PickLogic):

    def __init__(self, dto: TrailPickDto):
        super().__init__(dto)

    def calc_compared_rate(self, ts: TradeSet) -> float:
        bamt = ts.buy.totalAmount
        samt = ts.sell.totalAmount
        if bamt <0 or samt<0 :
            return 0
        return bamt / samt

    def get_amt(self, ts: TradeSet) -> float:
        return ts.buy.totalAmount

    def get_last_price(self, ts: TradeSet) -> float:
        return ts.buy.lastPrice


class ToSellLogic(PickLogic):

    def __init__(self, dto: TrailPickDto):
        super().__init__(dto)

    def get_amt(self, ts: TradeSet) -> float:
        return ts.sell.totalAmount

    def calc_compared_rate(self, ts: TradeSet) -> float:
        bamt = ts.buy.totalAmount
        samt = ts.sell.totalAmount
        if bamt <0 or samt<0 :
            return 0
        return samt / bamt

    def get_last_price(self, ts: TradeSet) -> float:
        return ts.sell.lastPrice
