from datetime import datetime
from typing import List, Dict, Any

import dateutil.parser
import pytz

from binance_f.model import Order, OrderSide
from binance_f import RequestClient
from market.Symbol import Symbol
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils


def get_order_side_amt(od: Order) -> float:
    return od.executedQty if od.side == OrderSide.BUY else - od.executedQty


class OrderFilter:

    def __init__(self, symbol: str = None, side: str = None, orderType: str = None, notOrderType: str = None,
                 tags: List[str] = list(),
                 untags: List[str] = list(),
                 excludeTags: List[str] = list(),
                 status: str = None,
                 group: List[str] = list(),
                 updateStartAt: str = None,
                 updateEndAt: str = None,
                 limit: int = None,
                 positionSide: str = None, **kwargs):
        self.symbol = symbol
        self.side = side
        self.positionSide = positionSide
        self.tags = tags
        self.untags = untags
        self.excludeTags = excludeTags
        self.orderType = orderType
        self.notOrderType = notOrderType
        self.status = status
        self.updateStartTime: int = dateutil.parser.parse(updateStartAt).timestamp() * 1000 if updateStartAt else None
        self.updateEndTime: int = dateutil.parser.parse(updateEndAt).timestamp() * 1000 if updateEndAt else None
        self.group: List[str] = group
        self.limit: int = limit

    def get_symbole(self):
        return Symbol.get(self.symbol)


class OrdersInfo:
    def __init__(self, orders: List[Order], group: str):
        self.lastAt: datetime = None
        self.origQty = 0
        self.avgPrice = 0
        self.orders: List[Order] = orders
        self.group: str = group
        self.groupMap: Dict[str, OrdersInfo] = dict()

    def subtotal(self):
        if len(self.orders) <= 0:
            return
        self.orders.sort(key=lambda s: s.updateTime, reverse=True)
        ups = self.orders[0].updateTime / 1000
        self.lastAt = datetime.fromtimestamp(ups, pytz.utc)
        sum_avg_price = 0
        for e in self.orders:
            e.updateAt = datetime.fromtimestamp(e.updateTime / 1000, pytz.utc).isoformat()
            self.origQty += e.origQty
            sum_avg_price += e.origQty * get_price(e)
        self.avgPrice = sum_avg_price / self.origQty
        if self.group:
            self.groupMap = self._group_by()

    def _group_by(self, ) -> Dict[str, object]:
        ans: Dict[str, OrdersInfo] = dict()
        for od in self.orders:
            groupv = getattr(od, self.group)
            g_sub_bundle = ans.get(groupv, OrdersInfo(group=None, orders=list()))
            g_sub_bundle.orders.append(od)
            ans[groupv] = g_sub_bundle
        for k, v in ans.items():
            v.subtotal()
        return ans

    def to_struct(self):
        # ans = {
        #     'lastAt': self.lastAt.isoformat() if self.lastAt else None,
        #     'executedQty': self.origQty
        # }
        # if self.group:
        #     ans['group'] = self.group
        #     ans['groupMap'] = dict()
        #     for k, v in self.groupMap.items():
        #         ans['groupMap'][k] = v.to_struct()
        # else:
        #     ans['orders'] = [o.__dict__ for o in self.orders]
        ans = comm_utils.to_dict(self)
        ans['lastAt'] = self.lastAt.isoformat() if self.lastAt else None
        return ans


class StatusMap:
    def __init__(self):
        self.map: Dict[str, OrdersInfo] = dict()

    def to_struct(self):
        ans = {}
        for k, v in self.map.items():
            ans[k] = v.to_struct()
        return ans


def fetch_order(client: RequestClient, pl: OrderFilter) -> OrdersInfo:
    oods: List[Order] = client.get_all_orders(symbol=pl.get_symbole().gen_with_usdt(), limit=pl.limit,
                                              startTime=pl.updateStartTime, endTime=pl.updateEndTime)
    return filter_order(oods, pl)


def filter_order_by_payload(oods: List[Order], payload: dict) -> Any:
    PayloadReqKey.clean_default_keys(payload)
    pl = OrderFilter(**payload)
    result = filter_order(oods, pl)
    return result.to_struct()


def filter_order(oods: List[Order], ft: OrderFilter) -> OrdersInfo:
    ans = OrdersInfo(group=ft.group[0] if ft.group else None, orders=list())
    for ods in oods:
        if ft.orderType and ods.type != ft.orderType:
            continue
        if ft.notOrderType and ods.type == ft.notOrderType:
            continue
        if ft.side and ods.side != ft.side:
            continue
        if ft.positionSide and ods.positionSide != ft.positionSide:
            continue
        if ft.symbol and ft.get_symbole().gen_with_usdt() != ods.symbol:
            continue
        if ft.status and ft.status != ods.status:
            continue
        if len(ft.tags) > 0 and not comm_utils.contains_tags(ods.clientOrderId, ft.tags):
            continue
        if len(ft.untags) > 0 and comm_utils.contains_tags(ods.clientOrderId, ft.untags):
            continue
        if len(ft.excludeTags) > 0 and comm_utils.contains_tags(ods.clientOrderId, ft.excludeTags):
            continue
        if ft.updateStartTime and ods.updateTime < ft.updateStartTime:
            continue
        if ft.updateEndTime and ods.updateTime > ft.updateEndTime:
            continue
        ans.orders.append(ods)
    ans.subtotal()
    return ans


def sum_amt(ods: List[Order]) -> float:
    ans = 0
    for od in ods:
        ans += od.origQty
    return ans


def get_price(od: Order) -> float:
    if od.avgPrice > 0:
        return od.avgPrice
    if od.price > 0:
        return od.price
    if od.stopPrice > 0:
        return od.stopPrice
    raise NotImplementedError(f'the {od} not support any price')


def combined_order_info(a: OrdersInfo, b: OrdersInfo) -> OrdersInfo:
    com_ods: List[Order] = list()
    com_ods.extend(a.orders)
    com_ods.extend(b.orders)
    ans: OrdersInfo = OrdersInfo(
        orders=com_ods, group=None
    )
    ans.subtotal()
    return ans
