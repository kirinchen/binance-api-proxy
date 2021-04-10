from binance_f import RequestClient
from binance_f.model import AccountInformation


def run(client: RequestClient, payload: dict):
    result: AccountInformation = client.get_account_information()
    result.assets = None
    result.positions = None
    return result.__dict__

