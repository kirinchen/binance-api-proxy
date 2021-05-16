import datetime

from binance_f import SubscriptionClient
from market.Symbol import Symbol
from rest import subscribeaggregatetrade, trade_pick
from rest.trade_pick import pick_logic
from utils.trade_utils import TradeSet


class TrailPickDto:
    def __init__(self, timeout: float, symbol: str, side: str, triggerAmt: float, timeGrpRange: float,
                 timeGrpSize: int, rsi:float):
        self.timeout = timeout  # senconds
        self.symbol: Symbol = Symbol.get(symbol)
        self.side = side
        self.triggerAmt = triggerAmt
        self.timeGrpRange = timeGrpRange  # seconds 1
        self.timeGrpSize = timeGrpSize
        self.rsi = rsi


class TrailPicker:

    def __init__(self, subClient: SubscriptionClient, dto: TrailPickDto):
        self.dto: TrailPickDto = dto
        self.subClient: SubscriptionClient = subClient
        self.startAt = datetime.datetime.now().timestamp()
        self.logic: pick_logic.PickLogic = trade_pick.gen_logic(self.dto)

    def trail(self) -> TradeSet:
        ts = subscribeaggregatetrade.subscript(self.subClient, self.dto.symbol, self.on_chek, self.dto.timeout)
        print(ts)
        return ts

    def on_chek(self, ts: TradeSet) -> bool:
        cat = datetime.datetime.now().timestamp()

        if self.logic.on_check(ts):
            return True
        dt = cat - self.startAt
        return dt > self.dto.timeout
