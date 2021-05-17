import threading
from datetime import datetime, timedelta, timezone

from binance_f import RequestClient, SubscriptionClient
from rest import get_aggregate_trades_list
from rest.poxy_controller import PayloadReqKey, gen_ws_client
from rest.trade_pick.trail_picker import TrailPickDto, TrailPicker
from utils.trade_utils import TradeSet


def run(client: RequestClient, payload: dict):
    def _job():
        try:
            PayloadReqKey.clean_default_keys(payload)
            with gen_ws_client(payload) as sub_client:
                sub_client: SubscriptionClient = sub_client
                tpd = TrailPickDto(**payload)

                tpicker = TrailPicker(client=client, subClient=sub_client, dto=tpd)
                ts = tpicker.trail()
        except Exception as e:
            print(e)

    t = threading.Thread(target=_job)
    t.start()

    return {}
