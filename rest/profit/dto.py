from market.Symbol import Symbol


class CutProfitDto:
    def __init__(self, symbol: str, profitRate: float, topRate: float, cutCount: int, positionSide: str):
        self.profitRate = profitRate
        self.topRate = topRate
        self.cutCount = cutCount
        self.symbol: Symbol = Symbol.get(symbol)
        self.positionSide: str = positionSide