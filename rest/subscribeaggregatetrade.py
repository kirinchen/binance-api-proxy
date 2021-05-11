import logging
from typing import List

from binance_f import SubscriptionClient, RequestClient
from binance_f.constant.test import *
from binance_f.model import *
from binance_f.exception.binanceapiexception import BinanceApiException

from binance_f.base.printobject import *
from infr.count_down_latch import CountDownLatch
from market.Symbol import Symbol
from rest.poxy_controller import gen_ws_client, PayloadReqKey
from utils import trade_utils
from utils.trade_utils import TradeSet, TradeEvent

logger = logging.getLogger("binance-client")
logger.setLevel(level=logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class Payload:

    def __init__(self, symbol: str):
        self.symbol: Symbol = Symbol.get(symbol)


def run(client: RequestClient, payload: dict):
    with gen_ws_client(payload) as sub_client:
        sub_client: SubscriptionClient = sub_client
        latch = CountDownLatch(300)
        tlist= TradeSet()

        def callback(data_type: 'SubscribeMessageType', event: 'any'):
            if data_type == SubscribeMessageType.RESPONSE:
                print("Event ID: ", event)
                # latch.count_down()
            elif data_type == SubscribeMessageType.PAYLOAD:
                event: AggregateTradeEvent = event
                # PrintBasic.print_obj(event)
                tlist.append(TradeEvent( event))
                tlist.subtotal()
                print(f's:{tlist.sell.totalAmount} b:{tlist.buy.totalAmount}')
                latch.count_down()
                # sub_client.unsubscribe_all()
            else:
                print("Unknown Data:")
            print()

        def error(e: 'BinanceApiException'):
            print(e.error_code + e.error_message)

        PayloadReqKey.clean_default_keys(payload)
        pl = Payload(**payload)
        sub_client.subscribe_aggregate_trade_event(pl.symbol.gen_with_usdt().lower(), callback, error)
        latch.wait()
        return tlist.to_struct()
