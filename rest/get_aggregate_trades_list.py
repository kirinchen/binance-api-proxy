from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model import Trade
from market.Symbol import Symbol
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils, trade_utils


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    sbl: Symbol = Symbol.get(payload.get('symbol'))
    startTime = payload.get('startTime')
    endTime = payload.get('endTime')
    result = client.get_aggregate_trades_list(symbol= sbl.gen_with_usdt(),startTime=startTime,endTime=endTime)
    ans = trade_utils.gen_subtotal_result( trade_utils.convert_traded_info( result))
    return ans.to_struct()