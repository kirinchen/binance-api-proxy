from binance_f import RequestClient
from binance_f.model import OrderSide, OrderType, TimeInForce, WorkingType, PositionSide
from rest.poxy_controller import PayloadReqKey


def run(client: RequestClient, payload: dict):
    for k in PayloadReqKey.values():
        del payload[k.value]
    _test(**payload)

    od = {
        "price": 30.8,
        "side": OrderSide.SELL,
        "symbol": "ETCUSDT",
        "timeInForce": TimeInForce.GTC,
        "ordertype": OrderType.LIMIT,
        "workingType": WorkingType.CONTRACT_PRICE,
        "positionSide": PositionSide.SHORT,
        "activationPrice": None,
        "closePosition": False,
        "quantity": 1
    }

    result = client.post_order(**od)
    return {}


def _test(a: str, b: int, c: str):
    print(f'{a}{b}{c}')
