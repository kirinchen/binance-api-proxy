from binance_f import RequestClient
from rest.position.stop.stop_mediation import StopMediationDto, StopMediation
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils


def run(client: RequestClient, payload: dict):
    try:
        PayloadReqKey.clean_default_keys(payload)
        dto = StopMediationDto(**payload)
        stopMediation = StopMediation(client=client, dto=dto)

        return comm_utils.to_dict(stopMediation.stop())
    except Exception as e:  # work on python 3.x
        return str(e)


