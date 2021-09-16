from typing import List

from binance_f import RequestClient
from binance_f.model import Order
from utils import order_utils
from utils.order_utils import filter_order_by_payload, OrderFilter


def run(client: RequestClient, payload: dict):
    order_filter: OrderFilter = OrderFilter(**payload)
    fetched_bundle = order_utils.fetch_order(client, order_filter)
    amt = order_utils.sum_amt(fetched_bundle.orders)
    return amt
