from typing import List

from utils.trade_utils import TradeInfo, TradeRange


class Amplitude:

    def __init__(self):
        self.sum: float = 0
        self.avg: float = 0

    def subtotal(self, n: int):
        self.avg = self.sum / n


class RSIResult:

    def __init__(self):
        self.rise = Amplitude()
        self.fall = Amplitude()
        self.groupNum = 0

    def subtotal(self, n: int):
        self.rise.subtotal(n)
        self.fall.subtotal(n)
        self.groupNum = n

    def calc_rsi(self) -> float:
        all = self.rise.avg + self.fall.avg
        d = self.rise.avg-self.fall.avg
        print(f'd:{d} all:{all}')
        return d / all


class RSIer:

    def __init__(self, trades: List[TradeInfo], grpSize: int):
        self.trades: List[TradeInfo] = trades
        self.grpSize: int = grpSize
        self.timeGrp: List[TradeRange] = self.split_grp()
        self.riseFall: RSIResult = None

    def calc(self) -> RSIResult:
        self.riseFall = self.calc_rise_fall_amplitude_avg()
        return self.riseFall

    def calc_rise_fall_amplitude_avg(self) -> RSIResult:
        ans = RSIResult()
        n = len(self.timeGrp)
        for i in range(n):
            if i > 0:
                ad = self.calc_amplitude(i)
                # print(f'ad={ad}')
                if ad > 0:
                    ans.rise.sum += ad
                else:
                    ans.fall.sum += ad * -1
        ans.subtotal(n)
        return ans

    def calc_amplitude(self, idx: int):
        last: TradeRange = self.timeGrp[idx - 1]
        cur: TradeRange = self.timeGrp[idx]
        last.subtotal()
        cur.subtotal()
        davg = cur.avgPrice - last.avgPrice
        return (davg / last.avgPrice)*100

    def split_grp(self) -> List[TradeRange]:
        ans: List[TradeRange] = list()
        ans.append(TradeRange())
        that = self.trades[0].time() + self.grpSize
        for t in self.trades:
            if t.time() > that:
                ans[-1].subtotal()
                that += self.grpSize
                ans.append(TradeRange())
            ans[-1].trades.append(t)
        return ans


# grpSize minseconds 1*1000
def gen_rsi(trades: List[TradeInfo], grpSize: int) -> RSIResult:
    rer = RSIer(trades, grpSize)
    return rer.calc()
