from binance_f import RequestClient
from rest.order.dto import OrderStrategy, TakeProfitDto, LimitDto
from rest.order.order_builder import BaseOrderBuilder
from rest.order.strategy.limit_order_builder import LimitOrderBuilder
from rest.order.strategy.take_profit_order_builder import TakeProfitOrderBuilder
from utils import comm_utils


def gen_order_builder(client: RequestClient, payload: dict) -> BaseOrderBuilder:
    strategy: str = payload.get('strategy')
    strategy: OrderStrategy = comm_utils.value_of_enum(OrderStrategy, strategy)
    return {
        OrderStrategy.TAKE_PROFIT: TakeProfitOrderBuilder(client=client, dto=TakeProfitDto(**payload)),
        OrderStrategy.LIMIT: LimitOrderBuilder(client=client, dto=LimitDto(**payload))
    }.get(strategy)
