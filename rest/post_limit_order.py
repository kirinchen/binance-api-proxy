from typing import List

from binance_f import RequestClient
from binance_f.model import AccountInformation, Position, TimeInForce, OrderType, WorkingType, Order
from market.Symbol import Symbol
from rest import get_recent_trades_list
from rest.position.stop import position_stop_utils
from rest.poxy_controller import PayloadReqKey
from utils import direction_utils, position_utils, comm_utils
from utils.comm_utils import fix_precision


def run(client: RequestClient, payload: dict):
    try:
        PayloadReqKey.clean_default_keys(payload)
        return comm_utils.to_dict(post_limit_order(client=client, **payload))
    except Exception as e:  # work on python 3.x
        return str(e)


def _calc_quantity(account: AccountInformation, quote: float, withdrawAmountRate: float, position: Position) -> float:
    amount = account.maxWithdrawAmount * withdrawAmountRate
    max_ratio = position.maxNotionalValue / amount
    ratio = min(max_ratio, position.leverage)
    quantity = (amount * ratio) / quote
    return quantity


def post_limit_order(client: RequestClient, positionSide: str, symbol: str, tags: List[str],
                     withdrawAmountRate: float, price: float = None) -> Order:
    symbol: Symbol = Symbol.get(symbol)
    account: AccountInformation = client.get_account_information()
    lastPrice = get_recent_trades_list.get_last_price(client=client, symbol=symbol)
    lastPrice = direction_utils.rise_price(positionSide, lastPrice, 1.0001)
    position: Position = position_utils.find_position(client=client, symbol=symbol.symbol, positionSide=positionSide)
    p: float = direction_utils.get_high_price(positionSide, lastPrice, price)
    qty: float = _calc_quantity(account=account, quote=p, withdrawAmountRate=withdrawAmountRate, position=position)

    price = fix_precision(symbol.precision_price, p)
    quantity_str = fix_precision(symbol.precision_amount, qty)
    return client.post_order(price=price,
                             side=direction_utils.get_limit_order_side(positionSide),
                             symbol=f'{symbol.symbol}USDT',
                             timeInForce=TimeInForce.GTC,
                             ordertype=OrderType.LIMIT,
                             workingType=WorkingType.CONTRACT_PRICE,
                             positionSide=positionSide,
                             # activationPrice=None,
                             # closePosition=False,
                             quantity=quantity_str,
                             newClientOrderId=comm_utils.get_order_cid(tags=tags)
                             )
