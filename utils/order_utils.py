from datetime import datetime
from typing import List, Dict, Any

import pytz

from binance_f.model import Order
from infr.constant import ORDER_CLASSIFLY_KEY
from market.Symbol import Symbol
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils


class OrderFilter:

    def __init__(self, symbol: str = None, side: str = None, orderType: str = None, tags: List[str] = list()):
        self.symbol = symbol
        self.side = side
        self.tags = tags
        self.orderType = orderType

    def get_symbole(self):
        return Symbol.get(self.symbol)


class SubtotalBundle:
    def __init__(self):
        self.lastAt: datetime = None
        self.orders: List[Order] = list()

    def subtotal(self):
        if len(self.orders) <=0:
            return
        self.orders.sort(key=lambda s: s.updateTime, reverse=True)
        ups = self.orders[0].updateTime / 1000
        self.lastAt = datetime.fromtimestamp(ups, pytz.utc)

    def to_struct(self):
        return {
            'lastAt': self.lastAt.isoformat() if self.lastAt else None,
            'orders': [o.__dict__ for o in self.orders]
        }


class StatusMap:
    def __init__(self):
        self.map: Dict[str, SubtotalBundle] = dict()

    def to_struct(self):
        ans = {}
        for k, v in self.map.items():
            ans[k] = v.to_struct()
        return ans


def filter_order_by_payload(oods: List[Order], payload: dict) -> Any:
    PayloadReqKey.clean_default_keys(payload)
    pl = OrderFilter(**payload)
    result = filter_order(oods, pl)
    cb: bool = payload.get(ORDER_CLASSIFLY_KEY)
    if cb:
        cmap = classify_by_status(result)
        return cmap.to_struct()
    else:
        return result.to_struct()


def filter_order(oods: List[Order], ft: OrderFilter) -> SubtotalBundle:
    ans = SubtotalBundle()
    for ods in oods:
        if ft.orderType and ods.type != ft.orderType:
            continue
        if ft.side and ods.side != ft.side:
            continue
        if ft.symbol and ft.get_symbole().gen_with_usdt() != ods.symbol:
            continue
        if len(ft.tags) > 0 and not comm_utils.contains_tags(ods.clientOrderId, ft.tags):
            continue
        ans.orders.append(ods)
    ans.subtotal()
    return ans


def classify_by_status(sb: SubtotalBundle) -> StatusMap:
    ans = StatusMap()
    for od in sb.orders:
        if od.status not in ans.map:
            ans.map[od.status] = SubtotalBundle()
        ans.map[od.status].orders.append(od)
    for k, v in ans.map.items():
        v.subtotal()
    return ans
