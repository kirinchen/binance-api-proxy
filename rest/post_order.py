from enum import Enum
import uuid
from binance_f import RequestClient
from binance_f.model import OrderSide, OrderType, TimeInForce, WorkingType, PositionSide, AccountInformation
from rest.poxy_controller import PayloadReqKey


class PayloadKey(Enum):
    investedRate = 'investedRate'
    guardRange = 'guardRange'
    quote = 'quote'
    symbol = 'symbol'


def _get_val(payload: dict, k: PayloadKey):
    return payload[k.value]


def fix_precision(fv: float):
    ans = float('{:.2f}'.format(fv))
    return str(ans)


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    account: AccountInformation = client.get_account_information()
    leverage_ratio = _get_val(payload, PayloadKey.investedRate) / _get_val(payload, PayloadKey.guardRange)
    amount = account.maxWithdrawAmount
    quote = _get_val(payload, PayloadKey.quote)
    quantity = (amount * leverage_ratio) / quote
    max_stop = quote * (1 + _get_val(payload, PayloadKey.guardRange))

    # od = {
    #     TODO ID
    #     "price": fix_precision(quote),
    #     "side": OrderSide.SELL,
    #     "symbol": "ETCUSDT",
    #     "timeInForce": TimeInForce.GTC,
    #     "ordertype": OrderType.LIMIT,
    #     "workingType": WorkingType.CONTRACT_PRICE,
    #     "positionSide": PositionSide.SHORT,
    #     "activationPrice": None,
    #     "closePosition": False,
    #     "quantity": fix_precision(quantity)
    # }

    oid = str(uuid.uuid4())

    result = client.post_order(price=fix_precision(quote),
                               side=OrderSide.SELL,
                               symbol=_get_val(payload, PayloadKey.symbol),
                               timeInForce=TimeInForce.GTC,
                               ordertype=OrderType.LIMIT,
                               workingType=WorkingType.CONTRACT_PRICE,
                               positionSide=PositionSide.SHORT,
                               activationPrice=None,
                               closePosition=False,
                               quantity=fix_precision(quantity),
                               newClientOrderId=oid
                               )

    result = client.post_order(
                               side=OrderSide.SELL,
                               symbol=_get_val(payload, PayloadKey.symbol),
                               timeInForce=TimeInForce.GTC,
                               ordertype=OrderType.TAKE_PROFIT_MARKET ,
                               workingType=WorkingType.CONTRACT_PRICE,
                               positionSide=PositionSide.SHORT,
                               stopPrice=fix_precision(max_stop),
                               closePosition=False,
                               quantity=fix_precision(quantity)
                               )

    return {}


def _test(a: str, b: int, c: str):
    print(f'{a}{b}{c}')
