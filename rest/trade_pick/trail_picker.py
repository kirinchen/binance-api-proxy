import datetime

from binance_f import SubscriptionClient
from market.Symbol import Symbol
from rest import subscribeaggregatetrade
from rest.trade_pick.pick_logic import gen_logic, CheckedResult, PickLogic
from utils.trade_utils import TradeSet


class TrailPickDto:
    def __init__(self, timeout: float, symbol: str, side: str, triggerAmt: float):
        self.timeout = timeout  # senconds
        self.symbol: Symbol = Symbol.get(symbol)
        self.side = side
        self.triggerAmt = triggerAmt


class TrailPicker:

    def __init__(self, subClient: SubscriptionClient, dto: TrailPickDto):
        self.dto: TrailPickDto = dto
        self.subClient: SubscriptionClient = subClient
        self.startAt = datetime.datetime.now().timestamp()
        self.logic: PickLogic = gen_logic(self.dto)

    def trail(self):
        ts = subscribeaggregatetrade.subscript(self.subClient, self.dto.symbol, self.on_chek)

    def on_chek(self, ts: TradeSet) -> bool:
        cat = datetime.datetime.now().timestamp()

        if self.logic.on_check(ts):
            return True
        dt = cat - self.startAt
        return dt > self.dto.timeout
