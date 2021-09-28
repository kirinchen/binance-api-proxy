from typing import List

from binance_f import RequestClient
from binance_f.model import Position, Order, OrderType
from infr import constant
from market.Symbol import Symbol
from market.enums import OrderStatus
from rest.position.stop import position_stop_utils
from utils import order_utils
from utils.order_utils import OrderFilter, OrdersInfo


class OrderBuildLeave:

    def __init__(self):
        self.build: OrdersInfo = OrdersInfo(group=None, orders=list())
        self.leave: OrdersInfo = OrdersInfo(group=None, orders=list())


class PositionOrderFinder:

    def __init__(self, client: RequestClient, position: Position):
        self.position = position
        self.client = client
        self.orders: List[Order] = self._init_orders()

    def _init_orders(self) -> List[Order]:
        all_orders = order_utils.fetch_order(self.client, OrderFilter(
            symbol=Symbol.get_with_usdt(self.position.symbol).symbol,
            positionSide=self.position.positionSide,
            status=OrderStatus.FILLED.value
        ))
        sum_amt = 0
        ans: List[Order] = list()
        for od in all_orders.orders:
            sum_amt += order_utils.get_order_side_amt(od)
            ans.append(od)
            if not position_stop_utils.is_difference_over_range(sum_amt, self.position.positionAmt, constant.LIMIT_0_RATE):
                return ans

        raise TypeError('over scan all the orders' + str(self.position))

    def get_build_leave_order_info(self) -> OrderBuildLeave:
        ans = OrderBuildLeave()
        for od in self.orders:
            if od.type == OrderType.LIMIT:
                ans.build.orders.append(od)
            else:
                ans.leave.orders.append(od)
        ans.build.subtotal()
        ans.leave.subtotal()
        return ans
