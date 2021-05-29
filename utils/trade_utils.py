from abc import ABCMeta, abstractmethod
from datetime import datetime
from typing import List

from binance_f.model import Trade, AggregateTradeEvent


class TradeInfo(metaclass=ABCMeta):

    @abstractmethod
    def qty(self) -> float:
        pass

    @abstractmethod
    def price(self) -> float:
        pass

    @abstractmethod
    def get_data(self) -> object:
        pass

    @abstractmethod
    def time(self) -> int:
        pass

    @abstractmethod
    def isBuyerMaker(self) -> bool:
        pass


class TradeEvent(TradeInfo):

    def __init__(self, event: AggregateTradeEvent):
        self.data = event

    def qty(self) -> float:
        return self.data.qty

    def price(self) -> float:
        return self.data.price

    def get_data(self) -> object:
        return self.data

    def time(self) -> int:
        return self.data.time

    def isBuyerMaker(self) -> bool:
        return self.data.isBuyerMaker


class Tradeed(TradeInfo):

    def __init__(self, t: Trade):
        self.data = t

    def isBuyerMaker(self) -> bool:
        return self.data.isBuyerMaker

    def price(self) -> float:
        return self.data.price

    def get_data(self) -> object:
        return self.data

    def time(self) -> int:
        return self.data.time

    def qty(self) -> float:
        return self.data.qty


class TradeRange:
    def __init__(self):
        self.avgPrice = 0
        self.totalAmount = 0
        self.lastPrice = 0
        self.lastAt: datetime = None
        self.highPrice = 0
        self.highPriceAt: datetime = None
        self.lowPrice = 0
        self.lowPriceAt: datetime = None
        self.highAmount = 0
        self.highAmountAt: datetime = None
        self.trades: List[TradeInfo] = list()

    def subtotal(self):
        try:
            amt = 0
            sup = 0
            for t in self.trades:
                amt += t.qty()
                sup += t.qty() * t.price()
            self.totalAmount = amt
            self.avgPrice = sup / self.totalAmount
            hpe = self.clac_max('price')
            self.highPrice = hpe.price()
            self.highPriceAt = datetime.fromtimestamp(hpe.time() / 1000)
            lpe = self.clac_min('price')
            self.lowPrice = lpe.price()
            self.lowPriceAt = datetime.fromtimestamp(lpe.time() / 1000)
            hae = self.clac_max('qty')
            self.highAmount = hae.qty()
            self.highAmountAt = datetime.fromtimestamp(hae.time() / 1000)
            le = self.clac_max('time')
            self.lastPrice = le.price()
            self.lastAt = datetime.fromtimestamp(le.time() / 1000)
        except Exception as e:  # work on python 3.x
            print(e)

    def get_first(self) -> TradeInfo:
        return self.clac_min('time')

    def clac_max(self, f: str) -> TradeInfo:
        return max(self.trades, key=lambda x: getattr(x.get_data(), f))

    def clac_min(self, f: str) -> TradeInfo:
        return min(self.trades, key=lambda x: getattr(x.get_data(), f))

    def to_struct(self) -> dict:
        ans = dict()
        for k, v in self.__dict__.items():
            if k == 'trades':
                ans[k] = [r.get_data().__dict__ for r in self.trades]
                continue
            if type(v) == datetime:
                ans[k] = v.isoformat()
                continue

            ans[k] = v

        return ans


class TradeSet:
    def __init__(self):
        self.sell = TradeRange()
        self.buy = TradeRange()
        self.all = TradeRange()

    def subtotal(self):
        self.sell.subtotal()
        self.buy.subtotal()
        self.all.subtotal()

    def append(self, t: TradeInfo):
        if t.isBuyerMaker():
            self.buy.trades.append(t)
        else:
            self.sell.trades.append(t)
        self.all.trades.append(t)

    def to_struct(self) -> dict:
        return {
            'sell': self.sell.to_struct(),
            'buy': self.buy.to_struct()
        }


def convert_traded_info(ts: List[Trade]) -> List[TradeInfo]:
    return [Tradeed(t) for t in ts]


def convert_event_info(ts: List[AggregateTradeEvent]) -> List[TradeInfo]:
    return [TradeEvent(t) for t in ts]


def gen_subtotal_result(ts: List[TradeInfo]) -> TradeSet:
    ans = TradeSet()
    for t in ts:
        ans.append(t)
    ans.subtotal()
    return ans
