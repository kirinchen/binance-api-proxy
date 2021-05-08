from datetime import datetime
from typing import List

from binance_f.model import Trade


class Bundle:
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
        self.trades: List[Trade] = list()

    def subtotal(self):
        amt = 0
        sup = 0
        for t in self.trades:
            amt += t.qty
            sup += t.qty * t.price
        self.totalAmount = amt
        self.avgPrice = sup / self.totalAmount
        hpe = self.clac_max('price')
        self.highPrice = hpe.price
        self.highPriceAt = datetime.fromtimestamp(hpe.time/1000)
        lpe = self.clac_min('price')
        self.lowPrice = lpe.price
        self.lowPriceAt = datetime.fromtimestamp(lpe.time/1000)
        hae = self.clac_max('qty')
        self.highAmount = hae.qty
        self.highAmountAt = datetime.fromtimestamp(hae.time/1000)
        le = self.clac_max('time')
        self.lastPrice = le.price
        self.lastAt = datetime.fromtimestamp(le.time/1000)

    def clac_max(self, f: str):
        return max(self.trades, key=lambda x: getattr(x, f))

    def clac_min(self, f: str):
        return min(self.trades, key=lambda x: getattr(x, f))

    def to_struct(self) -> dict:
        ans = dict()
        for k, v in self.__dict__.items():
            if k == 'trades':
                ans[k] = [r.__dict__ for r in self.trades]
                continue
            if type(v) == datetime:
                ans[k] = v.isoformat()
                continue

            ans[k] = v

        return ans


class Result:
    def __init__(self):
        self.sell = Bundle()
        self.buy = Bundle()

    def subtotal(self):
        self.sell.subtotal()
        self.buy.subtotal()

    def to_struct(self) -> dict:
        return {
            'sell': self.sell.to_struct(),
            'buy': self.buy.to_struct()
        }


def gen_subtotal_result(ts: List[Trade]) -> Result:
    ans = Result()
    for t in ts:
        if t.isBuyerMaker:
            ans.buy.trades.append(t)
        else:
            ans.sell.trades.append(t)
    ans.subtotal()
    return ans
