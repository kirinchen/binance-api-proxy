from binance_f import RequestClient
from utils import comm_utils


def run(client: RequestClient, payload: dict):
    result: any= client.get_exchange_information()

    return comm_utils.to_dict(result)
