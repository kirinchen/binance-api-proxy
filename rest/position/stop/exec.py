from binance_f import RequestClient
from utils import order_utils
from utils.order_utils import OrderFilter


def run(client: RequestClient, payload: dict):
    order_filter: OrderFilter = OrderFilter(**payload)
    fetched_bundle = order_utils.fetch_order(client, order_filter)
    amt = order_utils.sum_amt(fetched_bundle.orders)
    return amt