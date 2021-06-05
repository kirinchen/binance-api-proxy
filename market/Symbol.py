from enum import Enum


class Symbol(Enum):

    def __init__(self, symbol: str, title: str, precision_price: int, precision_amount: int):
        self.symbol = symbol
        self.title = title
        self.precision_price = precision_price
        self.precision_amount = precision_amount

    BTC = ('BTC', 'bitcoin', 2, 3)
    BCH = ('BCH', 'Bitcoin Cash', 2, 3)
    ETH = ('ETH', 'ethereum', 2, 3)
    ETC = ('ETC', 'Ethereum Classic', 3, 2)
    LTC = ('LTC', 'Litecoin', 2, 3)
    XRP = ('XRP', 'XRP', 4, 1)
    EOS = ('EOS', 'EOS', 3, 1)
    BNB = ('BNB', 'Binance Coin', 3, 2)

    def gen_with_usdt(self) -> str:
        return f'{self.symbol}USDT'

    def get_min_amount(self):
        return 1 / pow(10, self.precision_amount)

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


