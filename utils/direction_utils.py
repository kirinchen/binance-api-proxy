from binance_f.model import PositionSide, OrderSide


def get_high_price(positionSide: str, a: float, b: float) -> float:
    """
    LONG : a = 100 , b = 50  -> a = 100
    SHORT : a = 100 , b = 50  -> b = 50
    """
    if a is None:
        return b
    if b is None:
        return a
    if positionSide == PositionSide.LONG:
        return max(a, b)
    elif positionSide == PositionSide.SHORT:
        return min(a, b)
    raise NotImplementedError('not support ' + str(positionSide))


def get_low_price(positionSide: str, a: float, b: float) -> float:
    """
    LONG : a = 100 , b = 50  -> a = 100
    SHORT : a = 100 , b = 50  -> b = 50
    """
    if a is None:
        return b
    if b is None:
        return a
    a = -a
    b = -b
    nv = get_high_price(positionSide, a, b)
    return -nv


def rise_price(positionSide: str, orgPrice: float, rate: float) -> float:
    """
    LONG : orgPrice = 100 -> 101
    SHORT : orgPrice = 100 -> 99
    """
    if positionSide == PositionSide.LONG:
        return orgPrice * rate
    elif positionSide == PositionSide.SHORT:
        return orgPrice / rate
    raise NotImplementedError('not support ' + str(positionSide))


def fall_price(positionSide: str, orgPrice: float, rate: float) -> float:
    """
    LONG : orgPrice = 100 -> 99
    SHORT : orgPrice = 100 -> 101
    """
    return rise_price(positionSide=positionSide, orgPrice=orgPrice, rate=1 / rate)


def is_valid_stop_price(positionSide: str, recent_price: float, stop_price: float) -> bool:
    if positionSide == PositionSide.LONG:
        return recent_price > stop_price
    elif positionSide == PositionSide.SHORT:
        return recent_price < stop_price
    raise NotImplementedError('not support ' + str(positionSide))


def get_stop_order_side(positionSide: str) -> str:
    if positionSide == PositionSide.SHORT:
        return OrderSide.BUY
    if positionSide == PositionSide.LONG:
        return OrderSide.SELL
    raise NotImplementedError(f'not support {positionSide}')


def get_limit_order_side(positionSide: str) -> str:
    if positionSide == PositionSide.SHORT:
        return OrderSide.SELL
    if positionSide == PositionSide.LONG:
        return OrderSide.BUY
    raise NotImplementedError(f'not support {positionSide}')
