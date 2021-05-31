from market.Symbol import Symbol


class CutProfitDto:
    def __init__(self, symbol: str, profitRate: float, topRate: float, cutCount: int, positionSide: str,
                 minStepRate: float, bottomRate:float):
        self.profitRate = profitRate
        self.topRate = topRate
        self.cutCount = cutCount
        self.symbol: Symbol = Symbol.get(symbol)
        self.positionSide: str = positionSide
        self.minStepRate: float = minStepRate
        self.bottomRate : float = bottomRate
