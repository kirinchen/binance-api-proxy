from abc import ABCMeta, abstractmethod

from rest.trade_pick.dtos import CheckedResult
from rest.trade_pick.trail_picker import TrailPickDto
from utils import rsi_utils
from utils.rsi_utils import RSIResult
from utils.trade_utils import TradeSet


class PickLogic(metaclass=ABCMeta):

    def __init__(self, dto: TrailPickDto):
        self.dto: TrailPickDto = dto
        self.result: CheckedResult = CheckedResult()

    def on_check(self, ts: TradeSet) -> bool:
        camt = ts.all.totalAmount
        self.result.amount = camt
        if camt < self.dto.triggerAmt:
            return False
        if not self.calc_rsi(ts):
            return False

        self.packResult(ts)
        return True

    def calc_rsi(self, ts: TradeSet) -> bool:
        try:
            rsir: RSIResult = rsi_utils.gen_rsi(ts.all.trades, self.dto.timeGrpRange * 1000)
            print(f'groupNum:{rsir.groupNum}')
            if rsir.groupNum < self.dto.timeGrpSize:
                return False
            rsi = self.calc_rsi_result(rsir)
            print(f'rsi:{rsi}')
            self.result.groupNum = rsir.groupNum
            self.result.rsi = rsi
            if rsi > 1:
                return False
            if not self.is_threshold(ts):
                return False
            return rsi > self.dto.rsi

        except Exception as e:  # work on python 3.x
            print(e)
            return False

    def packResult(self, ts: TradeSet):
        self.result.price = self.get_last_price(ts)
        self.result.moreRate = self.result.amount / self.dto.triggerAmt
        self.result.success = True

    @abstractmethod
    def is_threshold(self, ts: TradeSet) -> bool:
        pass

    @abstractmethod
    def is_selled(self) -> bool:
        pass

    @abstractmethod
    def calc_rsi_result(self, r: RSIResult) -> float:
        pass

    @abstractmethod
    def get_last_price(self, ts: TradeSet) -> float:
        pass


class ToBuyLogic(PickLogic):

    def __init__(self, dto: TrailPickDto):
        super().__init__(dto)

    def is_threshold(self, ts: TradeSet) -> bool:
        if self.dto.threshold is None:
            return True
        th_p = self.dto.threshold
        end_p = ts.buy.lastPrice
        return th_p > end_p

    def is_selled(self) -> bool:
        return False

    def get_last_price(self, ts: TradeSet) -> float:
        return ts.buy.lastPrice

    def calc_rsi_result(self, r: RSIResult) -> float:
        return r.calc_rsi()


class ToSellLogic(PickLogic):

    def __init__(self, dto: TrailPickDto):
        super().__init__(dto)

    def is_threshold(self, ts: TradeSet) -> bool:
        if self.dto.threshold is None:
            return True
        th_p = self.dto.threshold
        end_p = ts.sell.lastPrice * 1.003
        return th_p < end_p

    def get_last_price(self, ts: TradeSet) -> float:
        return ts.sell.lastPrice

    def calc_rsi_result(self, r: RSIResult) -> float:
        return r.calc_rsi() * -1

    def is_selled(self) -> bool:
        return True
