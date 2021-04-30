from enum import Enum
from typing import List

from binance_f import RequestClient
from binance_f.model import AccountInformation, Position


# https://jsoneditoronline.org/#right=local.loviyo&left=cloud.f6750ff5cdca439ab3f675020fe7c12f  get position
# https://jsoneditoronline.org/#right=local.loviyo&left=cloud.29d904609c7e464ab7327d7bef7d9b93  get open orders

class PayloadKey(Enum):
    topRate = 'topRate'  # 0.5
    cutCount = 'cutCount' # 1-999


def run(client: RequestClient, payload: dict):
    result: List[Position] = client.get_position()

    return result.__dict__


class Cuter:
    TODO
