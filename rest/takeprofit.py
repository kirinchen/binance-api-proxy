from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import List, Dict

from binance_f import RequestClient
from binance_f.model import AccountInformation, Position, Order

# https://jsoneditoronline.org/#right=local.loviyo&left=cloud.f6750ff5cdca439ab3f675020fe7c12f  get position
# https://jsoneditoronline.org/#right=local.loviyo&left=cloud.29d904609c7e464ab7327d7bef7d9b93  get open orders
from market.Symbol import Symbol


class ProfitEnoughError(Exception):
    pass


class Payload:
    def __init__(self, profitRate: float, topRate: float, cutCount: float):
        self.profitRate = profitRate
        self.topRate = topRate
        self.cutCount = cutCount


class PositionOrders:

    def __init__(self):
        self.positions: List[Position] = list()
        self.orders: List[Order] = list();


class CutOrder:

    def __init__(self):
        self.position: Position = None
        self.orders: List[Order] = list()
        self.logic: CutLogic = None

    def setup_position(self, pos: Position):
        self.position = pos
        self.logic = gen_cut_logic(self)


class CutLogic(metaclass=ABCMeta):

    def __init__(self, cd: CutOrder):
        self.cutOrder = cd
        self.markPrice = self.cutOrder.position.markPrice
        self.entryPrice = self.cutOrder.position.entryPrice
        self.profitRate = -99999999

    def calc_bundle(self, payload: Payload):
        self.profitRate = self.calc_profit_rate()
        if self.profitRate < payload.profitRate:
            raise ProfitEnoughError(self.profitRate + '<' + payload.profitRate)

    @abstractmethod
    def calc_profit_rate(self) -> float:
        pass


class LongCutLogic(CutLogic):

    def calc_profit_rate(self) -> float:
        return ((self.markPrice - self.entryPrice) / self.entryPrice) - 1

    def __init__(self, cd: CutOrder):
        super().__init__(cd)


class ShortCutLogic(CutLogic):

    def __init__(self, cd: CutOrder):
        super().__init__(cd)

    def calc_profit_rate(self) -> float:
        return ((self.entryPrice - self.markPrice) / self.entryPrice) - 1


def gen_cut_logic(cd: CutOrder) -> CutLogic:
    return {
        'LONG': LongCutLogic(cd),
        'SHORT': ShortCutLogic(cd)
    }.get(cd.position.positionSide)


class Runner:

    def __init__(self, client: RequestClient):
        self.positions: List[Position] = client.get_position()
        self.openOrders: List[Order] = client.get_open_orders()
        self.cutOrderMap: Dict[str, Dict[Symbol, CutOrder]] = dict()
        self.cutOrderMap['LONG'] = Runner._gen_symbol_cutorders()
        self.cutOrderMap['SHORT'] = Runner._gen_symbol_cutorders()
        self._collect_positions()
        self._collect_orders()

    @staticmethod
    def _gen_symbol_cutorders() -> Dict[Symbol, CutOrder]:
        ans: Dict[Symbol, CutOrder] = dict()
        for sbl in Symbol:
            ans[sbl] = CutOrder()
        return ans

    def _collect_positions(self):
        for pos in self.positions:
            try:
                symbol = Symbol.get_with_usdt(pos.symbol)
                self.cutOrderMap[pos.positionSide][symbol].setup_position(pos)
            except KeyError:
                print("dont work")

    def _collect_orders(self):
        for ods in self.openOrders:
            try:
                symbol = Symbol.get_with_usdt(ods.symbol)
                self.cutOrderMap[ods.positionSide][symbol].orders.append(ods)
            except KeyError:
                print("dont work")


def run(client: RequestClient, payload: dict):
    runner = Runner(client)
    print(runner.cutOrderMap)
    return {}
