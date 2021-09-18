from binance_f import RequestClient
from rest.position.stop.loss.stop_loss import StopLossDto, StopLoss
from rest.poxy_controller import PayloadReqKey
from utils import order_utils
from utils.order_utils import OrderFilter


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    dto: StopLossDto = StopLossDto(**payload)
    stop_loss: StopLoss = StopLoss(client,dto)
    ps = stop_loss.get_current_position()
    pos = [r.__dict__ for r in ps]
    return pos