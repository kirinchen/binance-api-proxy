from datetime import datetime, timedelta, timezone

from binance_f import RequestClient, SubscriptionClient
from rest import get_aggregate_trades_list
from rest.poxy_controller import PayloadReqKey, gen_ws_client
from rest.trade_pick.trail_picker import TrailPickDto, TrailPicker
from utils.trade_utils import TradeSet


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    with gen_ws_client(payload) as sub_client:
        sub_client: SubscriptionClient = sub_client
        tpd = TrailPickDto(**payload)

        time = datetime.now(tz=timezone.utc)
        st = time.isoformat()
        etime = time + timedelta(seconds=10)
        et = etime.isoformat()
        tpd.timeout = 10

        tpicker = TrailPicker(subClient=sub_client, dto=tpd)
        ts = tpicker.trail()

        rts = get_aggregate_trades_list.get_list(client, tpd.symbol, st, et)
        print(st)
        print(et)
        printa(ts)
        printa(rts)

    return {
        "ws": ts.to_struct(),
        "rest": rts.to_struct()
    }


def printa(ts: TradeSet):
    print(f'{ts.buy.totalAmount} {ts.sell.totalAmount}')
