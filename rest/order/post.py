from binance_f import RequestClient
from rest.order import strategy
from rest.order.order_builder import BaseOrderBuilder
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils

def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    order_builder: BaseOrderBuilder = strategy.gen_order_builder(client=client, payload=payload)
    return comm_utils.to_dict(order_builder.post())
