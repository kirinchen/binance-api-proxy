from typing import List, Dict

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
from utils import trade_utils
from utils.trade_utils import TradeSet


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    sbl: Symbol = Symbol.get(payload.get('symbol'))
    limit = payload.get('limit')
    timeMaped: bool = payload.get('timeMaped', False)
    ts = fetch(client, sbl, limit, timeMaped)

    return ts.to_struct()


def fetch(client: RequestClient, sbl: Symbol, limit: int, timeMaped: bool = False) -> TradeSet:
    result: List[Trade] = client.get_recent_trades_list(symbol=f'{sbl.symbol}USDT', limit=limit)
    ans = trade_utils.gen_subtotal_result(trade_utils.convert_traded_info(result), timeMaped)
    return ans


def get_last_price(client: RequestClient, symbol: Symbol) -> float:
    data = fetch(client=client, sbl=symbol, limit=10, timeMaped=False)
    return data.all.lastPrice