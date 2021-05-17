import datetime
from typing import List

from binance_f import SubscriptionClient, RequestClient
from market.Symbol import Symbol
from rest import subscribeaggregatetrade, trade_pick, post_order
from rest.post_order import PostOrderDto
from rest.trade_pick import pick_logic
from rest.trade_pick.dtos import CheckedResult
from utils.trade_utils import TradeSet


class TrailPickDto:
    def __init__(self, timeout: float, symbol: str, side: str, triggerAmt: float, timeGrpRange: float,
                 timeGrpSize: int, rsi: float, investedRate: float, guardRange: float, tags: List[str],
                 currentMove: float = None
                 ):
        self.timeout = timeout  # senconds
        self.symbol: Symbol = Symbol.get(symbol)
        self.side = side
        self.triggerAmt = triggerAmt
        self.timeGrpRange = timeGrpRange  # seconds 1
        self.timeGrpSize = timeGrpSize
        self.rsi = rsi
        self.investedRate = investedRate
        self.guardRange = guardRange
        self.currentMove = currentMove
        self.tags: List[str] = tags


class TrailPicker:

    def __init__(self, client: RequestClient, subClient: SubscriptionClient, dto: TrailPickDto):
        self.dto: TrailPickDto = dto
        self.client = client
        self.subClient: SubscriptionClient = subClient
        self.startAt = datetime.datetime.now().timestamp()
        self.logic: pick_logic.PickLogic = trade_pick.gen_logic(self.dto)

    def trail(self) -> TradeSet:
        ts = subscribeaggregatetrade.subscript(self.subClient, self.dto.symbol, self.on_chek, self.dto.timeout)
        print(f'tr={ts}')
        rt = self.logic.result
        if rt:
            self.order(rt)
        return ts

    def order(self, r: CheckedResult):
        odto = PostOrderDto(tags=self.dto.tags, investedRate=self.dto.investedRate, guardRange=self.dto.guardRange,
                            symbol=self.dto.symbol.symbol, selled=self.logic.is_selled(), quote=r.price,
                            currentMove=self.dto.currentMove)
        print(odto.__dict__)
        post_order.post_order(client=self.client, pl=odto)

    def on_chek(self, ts: TradeSet) -> bool:
        cat = datetime.datetime.now().timestamp()

        if self.logic.on_check(ts):
            return True
        dt = cat - self.startAt
        print(f'{dt} {self.dto.timeout}')
        return dt > self.dto.timeout
