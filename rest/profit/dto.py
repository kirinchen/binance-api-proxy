from market.Symbol import Symbol


class CutProfitDto:
    def __init__(self, symbol: str, profitRate: float, topRate: float, cutCount: int, positionSide: str,
                 minStepRate: float, bottomRate: float, stepSizeRate: float = 0):
        self.profitRate = profitRate
        self.topRate = topRate
        self.cutCount = cutCount
        self.symbol: Symbol = Symbol.get(symbol)
        self.positionSide: str = positionSide
        self.minStepRate: float = minStepRate
        self.stepSizeRate: float = stepSizeRate
        self.bottomRate: float = bottomRate

    def to_dict(self) -> dict:
        ans = self.__dict__
        ans['symbol'] = self.symbol.symbol
        return ans
