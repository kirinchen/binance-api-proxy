from typing import List

from binance_f import RequestClient
from rest.position.stop.dto import StopResult
from rest.position.stop.guaranteed.stop_guaranteed import StopGuaranteedDto, StopGuaranteed
from rest.position.stop.loss.stop_loss import StopLossDto, StopLoss
from rest.position.stop.stoper import Stoper


class StopMediationDto:

    def __init__(self, symbol: str, positionSide: str, tags: List[str], stopLoss: dict, stopGuaranteed: dict):
        self.symbol: str = symbol
        self.positionSide: str = positionSide
        self.tags: List[str] = tags
        self._apply_default_fields(stopLoss)
        self.stopLoss = StopLossDto(**stopLoss)
        self._apply_default_fields(stopGuaranteed)
        self.stopGuaranteed = StopGuaranteedDto(**stopGuaranteed)

    def _apply_default_fields(self, dto: dict):
        dto.update({
            'symbol': self.symbol,
            'positionSide': self.positionSide,
            'tags': self.tags
        })


class StopMediation:

    def __init__(self, client: RequestClient, dto: StopMediationDto):
        self.client: RequestClient = client
        self.dto: StopMediationDto = dto
        self.stopLoss = StopLoss(client=self.client, dto=self.dto.stopLoss)
        self.stopGuaranteed = StopGuaranteed(client=self.client, dto=self.dto.stopGuaranteed)

    def stop(self) -> List[StopResult]:
        if self.stopGuaranteed.no_position:
            return [StopResult(noActiveMsg='no_position')]
        return self._stop_each([self.stopGuaranteed, self.stopLoss])

    def _stop_each(self, stops: List[Stoper]) -> List[StopResult]:
        no_stop_results: List[StopResult] = list()
        for stop in stops:
            stop.load_vars()
            stop_result: StopResult = stop.run()
            if stop_result.active:
                return [stop_result]
            else:
                no_stop_results.append(stop_result)

        return no_stop_results
