from enum import Enum


class Symbol(Enum):

    def __init__(self, symbol: str, title: str, precision_price: int, precision_amount: int, max_position_usdt: int):
        self.symbol = symbol
        self.title = title
        self.precision_price = precision_price
        self.precision_amount = precision_amount
        self.max_position_usdt = max_position_usdt

    BTC = ('BTC', 'bitcoin', 2, 3, 250000)
    BCH = ('BCH', 'Bitcoin Cash', 2, 3, 50000)
    ETH = ('ETH', 'ethereum', 2, 3, 10000)
    ETC = ('ETC', 'Ethereum Classic', 3, 2, 50000)
    LTC = ('LTC', 'Litecoin', 2, 3, 50000)
    XRP = ('XRP', 'XRP', 4, 1, 50000)
    EOS = ('EOS', 'EOS', 3, 1, 50000)
    BNB = ('BNB', 'Binance Coin', 2, 2, 50000)
    DOT = ('DOT', 'Polkadot', 3, 1, 50000)
    ADA = ('ADA', 'Cardano', 4, 0, 50000)

    def gen_with_usdt(self) -> str:
        return f'{self.symbol}USDT'

    def get_min_amount(self):
        return 1 / pow(10, self.precision_amount)

    def get_min_usd_amount(self, price: float) -> float:
        return price * self.get_min_amount()

    def fix_precision_price(self, price: float) -> float:
        fstr = str(self.precision_price) + 'f'
        return float(('{:.' + fstr + '}').format(price))

    def fix_precision_amt(self, amt: float) -> float:
        fstr = str(self.precision_amount) + 'f'
        return float(('{:.' + fstr + '}').format(amt))

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
