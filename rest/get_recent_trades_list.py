from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model import Trade
from market.Symbol import Symbol
from rest.poxy_controller import PayloadReqKey


# request_client = RequestClient(api_key=g_api_key, secret_key=g_secret_key)
#
# result = request_client.get_recent_trades_list(symbol="BTCUSDT", limit=10)
#
# print("======= Recent Trades List =======")
# PrintMix.print_data(result)
# print("==================================")


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    sbl: Symbol = Symbol.get(payload.get('symbol'))
    limit = payload.get('limit')
    ans = fetch(client, sbl, limit)
    return ans.to_struct()


class Bundle:
    def __init__(self):
        self.avgPrice = 0
        self.totalAmount = 0
        self.trades: List[Trade] = list()

    def subtotal(self):
        amt = 0
        sup = 0
        for t in self.trades:
            amt += t.qty
            sup += t.qty * t.price
        self.totalAmount = amt
        self.avgPrice = sup / self.totalAmount

    def to_struct(self) -> dict:
        return {
            'avgPrice': self.avgPrice,
            'totalAmount': self.totalAmount,
            'trades': [r.__dict__ for r in self.trades]
        }


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


def gen_result(ts: List[Trade]) -> Result:
    ans = Result()
    for t in ts:
        if t.isBuyerMaker:
            ans.buy.trades.append(t)
        else:
            ans.sell.trades.append(t)
    ans.subtotal()
    return ans


def fetch(client: RequestClient, sbl: Symbol, limit: int) -> Result:
    result: List[Trade] = client.get_recent_trades_list(symbol=f'{sbl.symbol}USDT', limit=limit)
    ans = gen_result(result)
    return ans
