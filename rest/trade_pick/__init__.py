from binance_f.model import OrderSide
from rest.trade_pick.pick_logic import PickLogic, ToSellLogic, ToBuyLogic
from rest.trade_pick.trail_picker import TrailPickDto


def gen_logic(dto: TrailPickDto) -> PickLogic:
    return {
        OrderSide.SELL: ToSellLogic(dto),
        OrderSide.BUY: ToBuyLogic(dto)
    }.get(dto.side)