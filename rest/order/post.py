from binance_f import RequestClient
from rest.order import strategy
from rest.order.order_builder import BaseOrderBuilder, LoadDataCheck
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    order_builder: BaseOrderBuilder = strategy.gen_order_builder(client=client, payload=payload)
    check_result: LoadDataCheck = order_builder.load_data()
    if not check_result.success:
        return comm_utils.to_dict(check_result)
    return comm_utils.to_dict(order_builder.post())
