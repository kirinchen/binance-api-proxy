from typing import List

from binance_f import RequestClient
from binance_f.model import Order
from utils.order_utils import filter_order_by_payload


def run(client: RequestClient, payload: dict):
    result: List[Order] = client.get_open_orders()
    return filter_order_by_payload(result, payload)
