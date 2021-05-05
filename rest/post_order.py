
from typing import List

from binance_f import RequestClient
from binance_f.model import OrderSide, OrderType, TimeInForce, WorkingType, PositionSide, AccountInformation, Order
from infr import constant
from market.Symbol import Symbol
from rest import get_recent_trades_list
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils
from utils.comm_utils import get_order_cid


class Payload:

    def __init__(self, tags: List[str], investedRate: float, guardRange: float, symbol: str, selled: bool,
                 quote: float = None,
                 currentMove: float = None):
        self.investedRate = investedRate
        self.guardRange = guardRange
        self.quote = quote
        self.symbol: Symbol = Symbol.get(symbol)
        self.selled = selled
        self.tags = tags
        self.currentMove = currentMove


def fix_precision(p: int, fv: float):
    fstr = str(p) + 'f'
    ans = float(('{:.' + fstr + '}').format(fv))
    return str(ans)


def calc_quote(client: RequestClient, pl: Payload) -> float:
    if pl.quote is None:
        cqr = get_recent_trades_list.fetch(client, pl.symbol, 200)
        cq = cqr.sell.avgPrice if pl.selled else cqr.buy.avgPrice
        rate = 1 + pl.currentMove if pl.selled else 1 - pl.currentMove
        return cq * rate
    else:
        return pl.quote


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    pl = Payload(**payload)
    account: AccountInformation = client.get_account_information()
    leverage_ratio = pl.investedRate / pl.guardRange
    amount = account.maxWithdrawAmount
    quote = calc_quote(client, pl)
    quantity = (amount * leverage_ratio) / quote
    if pl.selled:
        max_stop = quote * (1 + pl.guardRange)
    else:
        max_stop = quote * (1 - pl.guardRange)

    order_side = OrderSide.SELL if pl.selled else OrderSide.BUY
    stop_side = OrderSide.BUY if pl.selled else OrderSide.SELL

    order_position = PositionSide.SHORT if pl.selled else PositionSide.LONG

    oid = get_order_cid(pl.tags)
    price = fix_precision(pl.symbol.precision_price, quote)
    quantity_str = fix_precision(pl.symbol.precision_amount, quantity)
    result = client.post_order(price=price,
                               side=order_side,
                               symbol=f'{pl.symbol.symbol}USDT',
                               timeInForce=TimeInForce.GTC,
                               ordertype=OrderType.LIMIT,
                               workingType=WorkingType.CONTRACT_PRICE,
                               positionSide=order_position,
                               # activationPrice=None,
                               # closePosition=False,
                               quantity=quantity_str,
                               newClientOrderId=oid
                               )
    post_stop_order(client, oid, stop_side, pl.symbol, max_stop, quantity)

    return {
        "price": price,
        "stopPrice": max_stop,
        "quantity": quantity
    }


def post_stop_order(client: RequestClient, tags: List[str], stop_side: str, symbol: Symbol, stopPrice: float,
                    quantity: float) -> Order:
    stopPrice = fix_precision(symbol.precision_price, stopPrice)
    quantity = fix_precision(symbol.precision_amount, quantity)
    _tgs = [e for e in tags]
    _tgs.append(constant.STOP_MARKET_AUTO_LOSS_TAG)
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
        newClientOrderId=comm_utils.get_order_cid(_tgs)
    )
    return result


def _test(a: str, b: int, c: str):
    print(f'{a}{b}{c}')
