from typing import List

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *
from market.Symbol import Symbol

# request_client = RequestClient(api_key=g_api_key, secret_key=g_secret_key)
# result = request_client.cancel_order(symbol="BTCUSDT", orderId=534333508)
# PrintBasic.print_obj(result)
from utils import comm_utils


class Dto:

    def __init__(self, ids: List[str], symbol: str, **kwargs):
        self.ids: List[str] = ids
        self.symbol: str = symbol

    def get_symbole(self):
        return Symbol.get(self.symbol)


def run(client: RequestClient, payload: dict):
    dto = Dto(**payload)

    result = client.cancel_list_orders(symbol=dto.get_symbole().gen_with_usdt(),
                                       orderIdList=dto.ids)
    return comm_utils.to_struct_list(result)


def cancel_order(client: RequestClient, symbol: Symbol, orderId: int):
    client.cancel_order(symbol=f'{symbol.symbol}USDT', orderId=orderId)
