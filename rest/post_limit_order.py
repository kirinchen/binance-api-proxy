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
        if 'size' in payload:
            return comm_utils.to_dict(post_grid_limit_order(client=client, **payload))
        else:
            return comm_utils.to_dict(post_limit_order(client=client, **payload))
    except Exception as e:  # work on python 3.x
        return str(e)


def _calc_quantity(account: AccountInformation, quote: float, withdrawAmountRate: float, position: Position) -> float:
    amount = account.maxWithdrawAmount * withdrawAmountRate
    max_ratio = position.maxNotionalValue / amount
    ratio = min(max_ratio, position.leverage)
    quantity = (amount * ratio) / quote
    return quantity


def post_grid_limit_order(client: RequestClient, positionSide: str, symbol: str, tags: List[str],
                          withdrawAmountRate: float, size: int, gapRate, price: float = None) -> List[Order]:
    ans: List[Order] = list()
    per_withdrawAmountRate = withdrawAmountRate / size
    p = _opt_price(client=client, positionSide=positionSide, symbol=Symbol.get(symbol), price=price)
    for i in range(int(size)):
        r: float = 1 + (gapRate * i)
        per_price = direction_utils.fall_price(positionSide=positionSide, orgPrice=p, rate=r)
        ans.append(post_limit_order(client=client, positionSide=positionSide, symbol=symbol, tags=tags,
                                    withdrawAmountRate=per_withdrawAmountRate, price=per_price))
    return ans


def _opt_price(client: RequestClient, positionSide: str, symbol: Symbol, price: float = None) -> float:
    lastPrice = get_recent_trades_list.get_last_safe_limit_price(client=client, symbol=symbol,
                                                                 positionSide=positionSide)
    p: float = direction_utils.get_low_price(positionSide, lastPrice, price)
    return p


def post_limit_order(client: RequestClient, positionSide: str, symbol: str, tags: List[str],
                     withdrawAmountRate: float, price: float = None, forcePrice: bool = False) -> Order:
    symbol: Symbol = Symbol.get(symbol)
    account: AccountInformation = client.get_account_information()
    p: float = price if forcePrice else _opt_price(client=client, positionSide=positionSide, symbol=symbol, price=price)
    position: Position = position_utils.find_position(client=client, symbol=symbol.symbol, positionSide=positionSide)
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
