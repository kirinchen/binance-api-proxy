import datetime
import logging
import threading
from typing import List, Callable

import config
from binance_f import SubscriptionClient, RequestClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException

from binance_f.base.printobject import *
from client.fin_proxy_client import PointDto, post_multiple
from infr.count_down_latch import CountDownLatch
from market.Symbol import Symbol
from rest.poxy_controller import gen_ws_client, PayloadReqKey
from utils import trade_utils
from utils.trade_utils import TradeSet, TradeEvent, TradeRange
from threading import Timer

logger = logging.getLogger("binance-client")
logger.setLevel(level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class TrailTradeDto:

    def __init__(self, symbol: str, timeout: int, asynced: bool):
        self.symbol: Symbol = Symbol.get(symbol)
        self.timeout: int = timeout
        self.asynced: bool = asynced


def gen_point(sbl: Symbol, side: str, field: str, val: float, time: datetime, timeout: int) -> PointDto:
    return PointDto(
        measurement=config.env('fin-measurement'),
        tags={
            "symbol": sbl.symbol,
            "name": sbl.title,
            "category": 'cryptocurrency',
            "source": 'binance',
            "side": side.lower(),
            "trade": str(timeout) + 's'
        },
        field=field,
        val=val,
        time=time
    )


def gen_by_side(tr: TradeRange, side: str, sbl: Symbol, timeout: int) -> List[PointDto]:
    ans: List[PointDto] = list()
    ans.append(gen_point(sbl=sbl, side=side, field='totalAmount', val=tr.totalAmount, time=tr.lastAt, timeout=timeout))
    ans.append(gen_point(sbl=sbl, side=side, field='avgPrice', val=tr.avgPrice, time=tr.lastAt, timeout=timeout))
    ans.append(gen_point(sbl=sbl, side=side, field='lastPrice', val=tr.lastPrice, time=tr.lastAt, timeout=timeout))
    ans.append(gen_point(sbl=sbl, side=side, field='highPrice', val=tr.highPrice, time=tr.highPriceAt, timeout=timeout))
    ans.append(gen_point(sbl=sbl, side=side, field='lowPrice', val=tr.lowPrice, time=tr.lowPriceAt, timeout=timeout))
    ans.append(
        gen_point(sbl=sbl, side=side, field='highAmount', val=tr.highAmount, time=tr.highAmountAt, timeout=timeout))
    return ans


def collect_to_fin_srv(payload: dict):
    def _job():
        try:
            with gen_ws_client(payload) as sub_client:
                sub_client: SubscriptionClient = sub_client
                PayloadReqKey.clean_default_keys(payload)
                pl = TrailTradeDto(**payload)
                ts = collect(sub_client, pl)
                ps: List[PointDto] = list()
                ps.extend(gen_by_side(ts.sell, 'sell', pl.symbol, pl.timeout))
                ps.extend(gen_by_side(ts.buy, 'buy', pl.symbol, pl.timeout))
                post_multiple(ps)
                print('it ok send')
        except Exception as e:
            logging.error(e)

    t = threading.Thread(target=_job)
    t.start()
    return {}


def run(client: RequestClient, payload: dict):
    if payload["asynced"] == True:
        return collect_to_fin_srv(payload)
    with gen_ws_client(payload) as sub_client:
        sub_client: SubscriptionClient = sub_client
        PayloadReqKey.clean_default_keys(payload)
        pl = TrailTradeDto(**payload)
        return collect(sub_client, pl).to_struct()


def collect(sub_client: SubscriptionClient, pl: TrailTradeDto) -> TradeSet:
    startAt = datetime.datetime.now().timestamp()

    def check(ts: TradeSet) -> bool:
        cat = datetime.datetime.now().timestamp()
        dt = cat - startAt
        return pl.timeout <= dt

    tlist = subscript(sub_client, pl.symbol, check, delay=pl.timeout)
    return tlist


def subscript(sub_client: SubscriptionClient, symbol: Symbol, chek: Callable[[TradeSet], bool], delay=60) -> TradeSet:
    latch = CountDownLatch(1)
    tlist = TradeSet()

    def callback(data_type: 'SubscribeMessageType', event: 'any'):
        if data_type == SubscribeMessageType.RESPONSE:
            print("Event ID: ", event)
            # latch.count_down()
        elif data_type == SubscribeMessageType.PAYLOAD:
            event: AggregateTradeEvent = event
            tlist.append(TradeEvent(event))
            tlist.subtotal()
        else:
            print("Unknown Data:")
        if chek(tlist):
            latch.count_down()

    def error(e: 'BinanceApiException'):
        print(e.error_code + e.error_message)
        tlist.sell = None
        tlist.buy = None
        latch.count_down()

    sub_client.subscribe_aggregate_trade_event(symbol.gen_with_usdt().lower(), callback, error)

    def delay_stop(delay):
        print(f'foo() called after {delay}s delay')
        latch.count_down()

    t = Timer(delay, delay_stop, [delay])
    t.start()

    latch.wait()
    return tlist
