from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model import Trade
from market.Symbol import Symbol
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils, trade_utils
from utils.trade_utils import TradeSet


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    sbl: Symbol = Symbol.get(payload.get('symbol'))
    startTime = payload.get('startTime')
    endTime = payload.get('endTime')
    ans = get_list(client, sbl, startTime, endTime)
    return ans.to_struct()


def get_list(client: RequestClient, symbol: Symbol, startTime: str, endTime: str) -> TradeSet:
    result = client.get_aggregate_trades_list(symbol=symbol.gen_with_usdt(), startTime=startTime, endTime=endTime,
                                              limit=999)
    ans = trade_utils.gen_subtotal_result(trade_utils.convert_traded_info(result))
    return ans
