import logging
import datetime
from typing import List

import config
from binance_f import SubscriptionClient, RequestClient
from client.fin_proxy_client import PointDto, post_multiple
from market.Symbol import Symbol
from rest import subscribeaggregatetrade, trade_pick, post_order
from rest.post_order import PostOrderDto
from rest.trade_pick import pick_logic
from rest.trade_pick.dtos import CheckedResult
from utils.trade_utils import TradeSet


class TrailPickDto:
    def __init__(self, timeout: float, symbol: str, side: str, triggerAmt: float, timeGrpRange: float,
                 timeGrpSize: int, rsi: float, investedRate: float, guardRange: float, tags: List[str],
                 threshold: float = None, currentMove: float = None):
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
        self.threshold: float = threshold


class TrailPicker:

    def __init__(self, client: RequestClient, subClient: SubscriptionClient, dto: TrailPickDto):
        self.dto: TrailPickDto = dto
        self.client = client
        self.subClient: SubscriptionClient = subClient
        self.startAt = datetime.datetime.now().timestamp()
        self.logic: pick_logic.PickLogic = trade_pick.gen_logic(self.dto)
        self.point_dtos: List[PointDto] = list()

    def trail(self) -> TradeSet:
        self.log_start()
        ts = subscribeaggregatetrade.subscript(self.subClient, self.dto.symbol, self.on_chek, self.dto.timeout)
        rt = self.logic.result
        odto: PostOrderDto = None
        if rt.success:
            odto = self.order(rt)
        self.log_result(rt, odto, ts)
        self.add_success_tag(rt.success)
        post_multiple(self.point_dtos)
        return ts

    def add_success_tag(self, s: bool):
        for p in self.point_dtos:
            p.tags['success'] = str(s)

    def add_points(self, field: str, val: float, pickState: str, time: datetime, **kwargs):
        tags = {
            "symbol": self.dto.symbol.symbol,
            "name": self.dto.symbol.title,
            "category": 'cryptocurrency',
            "source": 'binance',
            "side": self.dto.side,
            "pickState": pickState
        }
        tags.update(**kwargs)
        p = PointDto(
            measurement=config.env('order-measurement'),
            tags=tags,
            field=field,
            val=val,
            time=time
        )
        self.point_dtos.append(p)

    def log_start(self):
        time = datetime.datetime.now(tz=datetime.timezone.utc)
        self.add_points(field='triggerAmt', val=self.dto.triggerAmt, pickState='start', time=time)
        self.add_points(field='rsi', val=self.dto.rsi, pickState='start', time=time)
        self.add_points(field='investedRate', val=self.dto.investedRate, pickState='start', time=time)
        self.add_points(field='guardRange', val=self.dto.guardRange, pickState='start', time=time)

    def log_result(self, r: CheckedResult, odto: PostOrderDto, ts: TradeSet):
        time = datetime.datetime.now(tz=datetime.timezone.utc)
        self.add_points(field='finalAmount', val=r.amount, pickState='result', time=time)
        self.add_points(field='finalRsi', val=r.rsi, pickState='result', time=time)
        self.add_points(field='startPrice', val=ts.all.get_first().price(), pickState='result', time=time)
        if odto is None:
            return
        self.add_points(field='quote', val=odto.quote, pickState='result', time=time)

    def order(self, r: CheckedResult) -> PostOrderDto:
        odto = PostOrderDto(tags=self.dto.tags, investedRate=self.dto.investedRate, guardRange=self.dto.guardRange,
                            symbol=self.dto.symbol.symbol, selled=self.logic.is_selled(), quote=r.price,
                            currentMove=self.dto.currentMove)
        logging.warning(odto.__dict__)
        post_order.post_order(client=self.client, pl=odto)
        return odto

    def on_chek(self, ts: TradeSet) -> bool:
        cat = datetime.datetime.now().timestamp()

        if self.logic.on_check(ts):
            return True
        dt = cat - self.startAt
        print(f'{dt} {self.dto.timeout}')
        return dt > self.dto.timeout
