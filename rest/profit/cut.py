from typing import List

from binance_f import RequestClient
from binance_f.model import Position, Order
# https://jsoneditoronline.org/#right=local.loviyo&left=cloud.f6750ff5cdca439ab3f675020fe7c12f  get position
# https://jsoneditoronline.org/#right=local.loviyo&left=cloud.29d904609c7e464ab7327d7bef7d9b93  get open orders
from market.Symbol import Symbol
from rest.poxy_controller import PayloadReqKey
from rest.profit.dto import CutProfitDto
from rest.profit.profit_cuter import ProfitCuter
from utils.position_utils import filter_position, PositionFilter


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    pl = CutProfitDto(**payload)
    result: List[Position] = client.get_position()
    pf = PositionFilter(symbol=pl.symbol.symbol, positionSide=pl.positionSide)
    p = filter_position(result, pf)[0]
    ods: List[Order] = client.get_open_orders()
    try:
        pc = ProfitCuter(pos=p, symbol=pl.symbol, orders=ods, payload=pl)
        pc.cut(client)
    except Exception as e:  # work on python 3.x
        return 'Failed to  ' + str(e)

    return {}
