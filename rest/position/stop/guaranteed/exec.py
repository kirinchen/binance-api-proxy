from binance_f import RequestClient
from rest.position.stop.guaranteed.stop_guaranteed import StopGuaranteedDto, StopGuaranteed
from rest.position.stop.loss.stop_loss import StopLossDto, StopLoss
from rest.poxy_controller import PayloadReqKey
from utils import order_utils
from utils.comm_utils import to_dict
from utils.order_utils import OrderFilter


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    dto: StopGuaranteedDto = StopGuaranteedDto(**payload)
    stop_guaranteed: StopGuaranteed = StopGuaranteed(client, dto)
    stop_guaranteed.load_vars()
    cb = stop_guaranteed.is_conformable()
    print(cb)
    result = stop_guaranteed.stop()
    return to_dict(result)
