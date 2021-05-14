from abc import ABCMeta, abstractmethod

from binance_f.model import OrderSide
from rest.trade_pick.trail_picker import TrailPickDto
from utils.trade_utils import TradeSet


class CheckedResult:

    def __init__(self, price: float, moreRate: float):
        self.price: float = price
        self.moreRate: float = moreRate


class PickLogic(metaclass=ABCMeta):

    def __init__(self, dto: TrailPickDto):
        self.dto: TrailPickDto = dto
        self.result: CheckedResult = None

    def on_check(self, ts: TradeSet) -> bool:
        camt = self.get_amt(ts)
        if camt


    @abstractmethod
    def get_amt(self, ts: TradeSet) -> float:
        pass


class ToBuyLogic(PickLogic):

    def __init__(self, dto: TrailPickDto):
        super().__init__(dto)

    def get_amt(self, ts: TradeSet) -> float:
        return ts.buy.totalAmount


class ToSellLogic(PickLogic):

    def __init__(self, dto: TrailPickDto):
        super().__init__(dto)

    def get_amt(self, ts: TradeSet) -> float:
        return ts.sell.totalAmount


def gen_logic(dto: TrailPickDto) -> PickLogic:
    return {
        OrderSide.SELL: ToSellLogic(dto),
        OrderSide.BUY: ToBuyLogic(dto)
    }.get(dto.side)
