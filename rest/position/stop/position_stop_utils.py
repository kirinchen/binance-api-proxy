from enum import Enum
from typing import List

from binance_f import RequestClient
from binance_f.model import OrderSide, PositionSide, Position, OrderType, Order
from market.Symbol import Symbol
from utils import order_utils
from utils.order_utils import SubtotalBundle, OrderFilter


class StopState(Enum):
    LOSS = 'LOSS'
    GUARANTEED = 'GUARANTEED'
    PROFIT = 'PROFIT'


def clac_guard_price(p: Position, guard_balance: float) -> float:
    return -(guard_balance / p.positionAmt) + p.entryPrice


def get_stop_order_side(positionSide: str) -> str:
    if positionSide == PositionSide.SHORT:
        return OrderSide.BUY
    if positionSide == PositionSide.LONG:
        return OrderSide.SELL
    raise NotImplementedError(f'not support {positionSide}')


def get_current_new_stop_orders(client: RequestClient, p: Position) -> (SubtotalBundle, float):
    symbol: Symbol = Symbol.get_with_usdt(p.symbol)
    stop_order_side: str = get_stop_order_side(p.positionSide)
    of = OrderFilter(symbol=symbol.symbol,
                     orderType=OrderType.STOP_MARKET,
                     status='NEW',
                     side=stop_order_side
                     )
    ans = order_utils.fetch_order(client, of)
    if ans.executedQty <= 0:
        return ans, 0
    sump = 0

    for o in ans.orders:
        sump += o.executedQty * o.stopPrice
    avgp = sump / ans.executedQty
    return ans, avgp


def is_difference_over_range(source: float, target: float, rate: float):
    r: float = 1 - (target / source)
    return r > rate


def clean_old_orders(client: RequestClient, symbol: Symbol, currentOds: List[Order]):
    try:
        if currentOds and len(currentOds) > 0:
            result = client.cancel_list_orders(symbol=symbol.gen_with_usdt(),
                                               orderIdList=[od.orderId for od in currentOds])
    except Exception as e:  # work on python 3.x
        print('Failed to upload to ftp: ' + str(e))
