import string
from enum import Enum
import uuid
import random

from binance_f import RequestClient
from binance_f.model import OrderSide, OrderType, TimeInForce, WorkingType, PositionSide, AccountInformation
from market.Symbol import Symbol
from rest.poxy_controller import PayloadReqKey


class PayloadKey(Enum):
    investedRate = 'investedRate'  # 0.5
    guardRange = 'guardRange'  # 0.02
    quote = 'quote'  # 600
    symbol = 'symbol'  # ETC BTC
    selled = 'selled'  # True / False


def _get_val(payload: dict, k: PayloadKey):
    return payload[k.value]


def fix_precision(p: int, fv: float):
    fstr = str(p) + 'f'
    ans = float(('{:.' + fstr + '}').format(fv))
    return str(ans)


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    selled: bool = _get_val(payload, PayloadKey.selled)
    account: AccountInformation = client.get_account_information()
    leverage_ratio = _get_val(payload, PayloadKey.investedRate) / _get_val(payload, PayloadKey.guardRange)
    amount = account.maxWithdrawAmount
    quote = _get_val(payload, PayloadKey.quote)
    quantity = (amount * leverage_ratio) / quote
    if selled:
        max_stop = quote * (1 + _get_val(payload, PayloadKey.guardRange))
    else:
        max_stop = quote * (1 - _get_val(payload, PayloadKey.guardRange))

    order_side = OrderSide.SELL if selled else OrderSide.BUY
    stop_side = OrderSide.BUY if selled else OrderSide.SELL

    order_position = PositionSide.SHORT if selled else PositionSide.LONG

    systr = _get_val(payload, PayloadKey.symbol)
    symbol = Symbol.get(systr)

    letters = string.ascii_letters
    oid = (''.join(random.choice(letters) for i in range(10)))
    price = fix_precision(symbol.precision_price, quote)
    quantity = fix_precision(symbol.precision_amount, quantity)
    result = client.post_order(price=price,
                               side=order_side,
                               symbol=f'{symbol.symbol}USDT',
                               timeInForce=TimeInForce.GTC,
                               ordertype=OrderType.LIMIT,
                               workingType=WorkingType.CONTRACT_PRICE,
                               positionSide=order_position,
                               # activationPrice=None,
                               # closePosition=False,
                               quantity=quantity,
                               newClientOrderId=oid
                               )
    stopPrice = fix_precision(symbol.precision_price, max_stop)
    result = client.post_order(
        side=stop_side,
        symbol=f'{symbol.symbol}USDT',
        timeInForce=TimeInForce.GTC,
        ordertype=OrderType.STOP_MARKET,
        workingType=WorkingType.CONTRACT_PRICE,
        positionSide=PositionSide.LONG,
        stopPrice=stopPrice,
        # closePosition=False,
        quantity=quantity,
        newClientOrderId="for" + oid
    )

    return {
        "price": price,
        "stopPrice": stopPrice,
        "quantity": quantity
    }


def _test(a: str, b: int, c: str):
    print(f'{a}{b}{c}')
