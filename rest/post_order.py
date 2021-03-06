from typing import List

from binance_f import RequestClient
from binance_f.model import OrderSide, OrderType, TimeInForce, WorkingType, PositionSide, AccountInformation, Order
from infr import constant
from market.Symbol import Symbol
from rest import get_recent_trades_list
from rest.poxy_controller import PayloadReqKey
from utils import comm_utils
from utils.comm_utils import get_order_cid, gen_group_uid, fix_precision


class PostOrderDto:

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





def calc_quote(client: RequestClient, pl: PostOrderDto) -> float:
    rate = 1 + pl.currentMove if pl.selled else 1 - pl.currentMove
    cur_quote = _get_current_quote(client, pl)
    if pl.quote is None:
        return cur_quote * rate
    else:
        order_quote = pl.quote * rate
        return _get_safe_quote(cur_quote, order_quote, pl.selled)


def _get_safe_quote(current_quote: float, order_quote: float, selled: bool) -> float:
    if selled:
        return max(current_quote, order_quote)
    else:
        return min(current_quote, order_quote)


def _get_current_quote(client: RequestClient, pl: PostOrderDto) -> float:
    cqr = get_recent_trades_list.fetch(client, pl.symbol, 200)
    cq = cqr.sell.avgPrice if pl.selled else cqr.buy.avgPrice
    return cq


def run(client: RequestClient, payload: dict):
    try:
        PayloadReqKey.clean_default_keys(payload)
        pl = PostOrderDto(**payload)
        return post_order(client, pl)
    except Exception as e:  # work on python 3.x
        return str(e)


def _calc_quantity(account: AccountInformation, quote: float, pl: PostOrderDto) -> float:
    leverage_ratio = pl.investedRate / pl.guardRange
    amount = account.maxWithdrawAmount

    max_ratio = pl.symbol.max_position_usdt / amount
    ratio = min(max_ratio, leverage_ratio)
    quantity = (amount * ratio) / quote
    return quantity


def post_order(client: RequestClient, pl: PostOrderDto):
    account: AccountInformation = client.get_account_information()
    quote = calc_quote(client, pl)

    order_side = OrderSide.SELL if pl.selled else OrderSide.BUY
    stop_side = OrderSide.BUY if pl.selled else OrderSide.SELL
    order_position = PositionSide.SHORT if pl.selled else PositionSide.LONG
    _calc_quantity(account, quote, pl)

    leverage_ratio = pl.investedRate / pl.guardRange
    amount = account.maxWithdrawAmount

    quantity = (amount * leverage_ratio) / quote
    if pl.selled:
        max_stop = quote * (1 + pl.guardRange)
    else:
        max_stop = quote * (1 - pl.guardRange)

    gid = gen_group_uid()
    pl.tags.append(gid)
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
    tags = pl.tags
    tags.append(constant.STOP_MARKET_AUTO_LOSS_TAG)
    post_stop_order(client, tags, stop_side, pl.symbol, max_stop, quantity)

    return {
        "price": price,
        "stopPrice": max_stop,
        "quantity": quantity
    }


def post_stop_order(client: RequestClient, tags: List[str], stop_side: str,
                    symbol: Symbol, stopPrice: float,
                    quantity: float) -> Order:
    positionSide = PositionSide.SHORT if stop_side == OrderSide.BUY else PositionSide.LONG

    stopPrice = fix_precision(symbol.precision_price, stopPrice)
    quantity = fix_precision(symbol.precision_amount, quantity)
    result = client.post_order(
        side=stop_side,
        symbol=f'{symbol.symbol}USDT',
        timeInForce=TimeInForce.GTC,
        ordertype=OrderType.STOP_MARKET,
        workingType=WorkingType.CONTRACT_PRICE,
        positionSide=positionSide,
        stopPrice=stopPrice,
        # closePosition=False,
        quantity=quantity,
        newClientOrderId=comm_utils.get_order_cid(tags)
    )
    return result
