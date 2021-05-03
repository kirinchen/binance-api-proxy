from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import List, Dict

from binance_f import RequestClient
from binance_f.model import AccountInformation, Position, Order, PositionSide, OrderSide, OrderType

# https://jsoneditoronline.org/#right=local.loviyo&left=cloud.f6750ff5cdca439ab3f675020fe7c12f  get position
# https://jsoneditoronline.org/#right=local.loviyo&left=cloud.29d904609c7e464ab7327d7bef7d9b93  get open orders
from market.Symbol import Symbol
from rest import post_order, cancel_order
from rest.poxy_controller import PayloadReqKey


class AmtPrice:
    def __init__(self, amt: float, price: float, newed: bool = False):
        self.amt = amt
        self.price = price
        self.newed = newed


class ProfitEnoughError(Exception):
    pass


class Payload:
    def __init__(self, profitRate: float, topRate: float, cutCount: int):
        self.profitRate = profitRate
        self.topRate = topRate
        self.cutCount = cutCount


class PositionOrders:

    def __init__(self):
        self.positions: List[Position] = list()
        self.orders: List[Order] = list()


class CutOrder:

    def __init__(self):
        self.position: Position = None
        self.stopOrders: List[Order] = list()
        self.logic: CutLogic = None
        self.symbol: Symbol = None

    def setup_position(self, pos: Position, symbol: Symbol):
        if pos.positionAmt <= 0:
            return
        self.position = pos
        self.symbol = symbol
        self.logic = gen_cut_logic(self)

    def cut(self, client: RequestClient, payload: Payload):
        if self.position and self.logic:
            self.logic.cut(client, payload)


class CutLogic(metaclass=ABCMeta):

    def __init__(self, cd: CutOrder):
        self.cutOrder = cd
        self.markPrice = self.cutOrder.position.markPrice
        self.entryPrice = self.cutOrder.position.entryPrice
        self.profitRate = -99999999
        self.stepPrices = list()
        self.stepQuantity = 0

    def _calc_bundle(self, payload: Payload):
        self.profitRate = self.calc_profit_rate()
        if self.profitRate < payload.profitRate:
            raise ProfitEnoughError(str(self.profitRate) + '<' + str(payload.profitRate))
        self.stepQuantity = self.cutOrder.position.positionAmt / payload.cutCount
        sp = self.calc_step_prices(payload.cutCount, payload.topRate)
        self._add_step_prices(sp)

    def _add_step_prices(self, ps: List[float]):
        sumQ = 0.0
        aps = self._list_amt_price(ps)
        for p in aps:
            if sumQ > self.cutOrder.position.positionAmt:
                return
            if p.newed:
                self.stepPrices.append(p.price)
            sumQ += p.amt

    def _list_amt_price(self, ps: List[float]) -> List[AmtPrice]:
        ans: List[AmtPrice] = list()
        for p in ps:
            ans.append(AmtPrice(self.stepQuantity, p, True))
        for ods in self.cutOrder.stopOrders:
            ans.append(AmtPrice(ods.origQty, ods.stopPrice, False))
        self.sort_amt_price(ans)
        return ans

    def cut(self, client: RequestClient, payload: Payload):
        try:
            self._calc_bundle(payload)
        except ProfitEnoughError:
            print("not over th")
            return
        for sp in self.stepPrices:
            nods = post_order.post_stop_order(client=client, symbol=self.cutOrder.symbol,
                                              stop_side=self.get_stop_side(),
                                              stopPrice=sp,
                                              quantity=self.stepQuantity)
            self.cutOrder.stopOrders.append(nods)
        self.clean_over_order(client)

    def clean_over_order(self, client: RequestClient):
        self.cutOrder.stopOrders.sort(key=lambda s: s.stopPrice, reverse=True)
        sumQ = 0.0
        for ods in self.cutOrder.stopOrders:
            if sumQ >= self.cutOrder.position.positionAmt:
                cancel_order.cancel_order(client, self.cutOrder.symbol, ods.orderId)
                continue
            sumQ += ods.origQty

    @abstractmethod
    def sort_amt_price(self, aps: List[AmtPrice]):
        pass

    @abstractmethod
    def get_stop_side(self) -> str:
        pass

    @abstractmethod
    def calc_profit_rate(self) -> float:
        pass

    @abstractmethod
    def calc_step_prices(self, cutCount: int, topRate: float) -> List[float]:
        pass


class LongCutLogic(CutLogic):

    def sort_amt_price(self, aps: List[AmtPrice]):
        aps.sort(key=lambda s: s.price)

    def get_stop_side(self) -> str:
        return OrderSide.SELL

    def calc_step_prices(self, cutCount: int, topRate: float) -> List[float]:
        ans: List[float] = list()
        dp = (self.markPrice - self.entryPrice) * topRate
        dsp = dp / cutCount
        for i in range(cutCount):
            p = (dsp * (i + 1)) + self.entryPrice
            ans.append(p)
        return ans

    def calc_profit_rate(self) -> float:
        return ((self.markPrice - self.entryPrice) / self.entryPrice) * self.cutOrder.position.leverage

    def __init__(self, cd: CutOrder):
        super().__init__(cd)


class ShortCutLogic(CutLogic):

    def sort_amt_price(self, aps: List[AmtPrice]):
        aps.sort(key=lambda s: s.price, reverse=True)

    def calc_step_prices(self, cutCount: int, topRate: float) -> List[float]:
        ans: List[float] = list()
        dp = (self.entryPrice - self.markPrice) * topRate
        dsp = dp / cutCount
        for i in range(cutCount):
            p = (dsp * (i + 1)) + self.markPrice
            ans.append(p)
        return ans

    def get_stop_side(self) -> str:
        return OrderSide.BUY

    def __init__(self, cd: CutOrder):
        super().__init__(cd)

    def calc_profit_rate(self) -> float:
        return (self.entryPrice - self.markPrice) / self.entryPrice


def gen_cut_logic(cd: CutOrder) -> CutLogic:
    return {
        PositionSide.LONG: LongCutLogic(cd),
        PositionSide.SHORT: ShortCutLogic(cd)
    }.get(cd.position.positionSide)


class Runner:

    def __init__(self, client: RequestClient, payload: Payload):
        self.payload = payload
        self.client = client
        self.positions: List[Position] = client.get_position()
        self.openOrders: List[Order] = client.get_open_orders()
        self.cutOrderMap: Dict[str, Dict[Symbol, CutOrder]] = dict()
        self.cutOrderMap[PositionSide.LONG] = Runner._gen_symbol_cutorders()
        self.cutOrderMap[PositionSide.SHORT] = Runner._gen_symbol_cutorders()
        self._collect_positions()
        self._collect_orders()

    def run_all(self):
        self.run_by_side(PositionSide.LONG)
        self.run_by_side(PositionSide.SHORT)

    def run_by_side(self, side: str):
        map: Dict[Symbol, CutOrder] = self.cutOrderMap[side]
        for e in Symbol:
            e: Symbol = e
            map[e].cut(self.client, self.payload)

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
                self.cutOrderMap[pos.positionSide][symbol].setup_position(pos, symbol)
            except KeyError:
                print("dont work")

    def _collect_orders(self):
        for ods in self.openOrders:
            if ods.type != OrderType.STOP_MARKET:
                continue
            try:
                symbol = Symbol.get_with_usdt(ods.symbol)
                side = ods.side
                pside = PositionSide.LONG if side == OrderSide.SELL else PositionSide.SHORT
                self.cutOrderMap[pside][symbol].stopOrders.append(ods)
            except KeyError:
                print("dont work")


def run(client: RequestClient, payload: dict):
    PayloadReqKey.clean_default_keys(payload)
    pl = Payload(**payload)
    runner = Runner(client, pl)
    runner.run_all()
    return {}
