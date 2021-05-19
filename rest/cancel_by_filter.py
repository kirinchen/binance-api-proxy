from typing import List

from binance_f.exception.binanceapiexception import BinanceApiException

from binance_f import RequestClient
from binance_f.constant.test import *
from binance_f.base.printobject import *
from binance_f.model.constant import *

# request_client = RequestClient(api_key=g_api_key, secret_key=g_secret_key)
# #result = request_client.cancel_list_orders(symbol="ETHUSDT", orderIdList = [459158679, 459159436, 10])
# result = request_client.cancel_list_orders(symbol="BTCUSDT", origClientOrderIdList = ["web_BL7xhx6cz2lDbVlbLCbQ", "web_tW94LJCxDRUSrXN19myG", "abc"])
# PrintList.print_object_list(result)
from market.Symbol import Symbol
from rest import get_open_orders
from rest.get_open_orders import OrderFilter
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils


def run(client: RequestClient, payload: dict):
    try:
        PayloadReqKey.clean_default_keys(payload)
        pl = OrderFilter(**payload)

        olist = get_open_orders.filter_order(client.get_open_orders(pl.get_symbole().gen_with_usdt()), pl)
        if len(olist.orders) <= 0:
            return

        ids = [e.orderId for e in olist.orders]

        result = client.cancel_list_orders(symbol=pl.get_symbole().gen_with_usdt(),
                                           orderIdList=ids)
        return comm_utils.to_struct_list(result)
    except BinanceApiException as e:  # work on python 3.x
        print('Failed to upload to ftp: ' + str(e))
        return e.__dict__
