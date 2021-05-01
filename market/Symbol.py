from enum import Enum


class Symbol(Enum):

    def __init__(self, symbol: str, precision_price: int, precision_amount: int):
        self.precision_price = precision_price
        self.precision_amount = precision_amount
        self.symbol = symbol

    BTC = ('BTC', 2, 3)
    BCH = ('BCH', 2, 3)
    ETH = ('ETH', 2, 3)
    ETC = ('ETC', 3, 2)
    LTC = ('LTC', 2, 3)
    XRP = ('XRP', 4, 1)
    EOS = ('EOS', 3, 1)
    BNB = ('BNB', 3, 2)

    @classmethod
    def values(cls):
        ans = [e for e in Symbol]
        return ans

    @classmethod
    def get(cls, systr: str):
        for _e in Symbol:
            e: Symbol = _e
            if e.symbol == systr:
                return e
        raise KeyError('Not find :' + systr)

    @classmethod
    def get_with_usdt(cls, s: str):
        s = s.replace('USDT', '')
        if s == 'BTC':
            print(s)
        return Symbol.get(s)
