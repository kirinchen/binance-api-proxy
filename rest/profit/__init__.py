from binance_f.model import PositionSide
from rest.profit.cut_logic import CutLogic, LongCutLogic, ShortCutLogic
from rest.profit.profit_cuter import ProfitCuter


def gen_cut_logic(cd: ProfitCuter) -> CutLogic:
    return {
        PositionSide.LONG: LongCutLogic(cd),
        PositionSide.SHORT: ShortCutLogic(cd)
    }.get(cd.position.positionSide)