import string
from enum import Enum
import uuid
import random

from binance_f import RequestClient
from binance_f.model import OrderSide, OrderType, TimeInForce, WorkingType, PositionSide, AccountInformation
from market.Symbol import Symbol
from rest.poxy_controller import PayloadReqKey


class PayloadKey(Enum):
    investedRate = 'investedRate'
    guardRange = 'guardRange'
    quote = 'quote'
    symbol = 'symbol'


def _get_val(payload: dict, k: PayloadKey):
    return payload[k.value]


def fix_precision(p: int, fv: float):
    fstr = str(p) + 'f'
    ans = float(('{:.' + fstr + '}').format(fv))
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
    systr = _get_val(payload, PayloadKey.symbol)
    symbol = Symbol.get(systr)

    letters = string.ascii_letters
    oid = (''.join(random.choice(letters) for i in range(10)))

    result = client.post_order(price=fix_precision(symbol.precision_price, quote),
                               side=OrderSide.SELL,
                               symbol=f'{symbol.symbol}USDT',
                               timeInForce=TimeInForce.GTC,
                               ordertype=OrderType.LIMIT,
                               workingType=WorkingType.CONTRACT_PRICE,
                               positionSide=PositionSide.SHORT,
                               activationPrice=None,
                               closePosition=False,
                               quantity=fix_precision(symbol.precision_amount, quantity),
                               newClientOrderId=oid
                               )

    result = client.post_order(
        side=OrderSide.BUY,
        symbol=f'{symbol.symbol}USDT',
        timeInForce=TimeInForce.GTC,
        ordertype=OrderType.STOP_MARKET,
        workingType=WorkingType.CONTRACT_PRICE,
        positionSide=PositionSide.SHORT,
        stopPrice=fix_precision(symbol.precision_price, max_stop),
        closePosition=False,
        quantity=fix_precision(symbol.precision_amount, quantity),
        newClientOrderId="for"+oid
    )

    return {}


def _test(a: str, b: int, c: str):
    print(f'{a}{b}{c}')
