from abc import ABCMeta, abstractmethod

from binance_f.model import OrderSide
from rest.trade_pick.trail_picker import TrailPickDto
from utils import rsi_utils
from utils.rsi_utils import RSIResult
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
        camt = ts.all.totalAmount

        if camt < self.dto.triggerAmt:
            return False
        if not self.calc_rsi(ts):
            return False

        self.packResult(ts, camt)
        return False

    def calc_rsi(self, ts: TradeSet) -> bool:
        try:
            rsir: RSIResult = rsi_utils.gen_rsi(ts.all.trades, self.dto.timeGrpRange * 1000)
            if rsir.groupNum < self.dto.timeGrpSize:
                return False
            rsi = self.calc_rsi(rsir)
            if rsi > 1 :
                return False
            if rsi > self.dto.rsi:
                return True
        except Exception as e:  # work on python 3.x
            print(e)
            return False

    def packResult(self, ts: TradeSet, camt: float):
        ans = CheckedResult(price=self.get_last_price(ts), moreRate=camt / self.dto.triggerAmt)
        return ans

    @abstractmethod
    def calc_rsi(self, r: RSIResult) -> float:
        pass

    @abstractmethod
    def get_last_price(self, ts: TradeSet) -> float:
        pass


class ToBuyLogic(PickLogic):

    def __init__(self, dto: TrailPickDto):
        super().__init__(dto)

    def get_last_price(self, ts: TradeSet) -> float:
        return ts.buy.lastPrice

    def calc_rsi(self, r: RSIResult) -> float:
        return r.calc_rsi()


class ToSellLogic(PickLogic):

    def __init__(self, dto: TrailPickDto):
        super().__init__(dto)

    def get_last_price(self, ts: TradeSet) -> float:
        return ts.sell.lastPrice

    def calc_rsi(self, r: RSIResult) -> float:
        return r.calc_rsi() * -1
