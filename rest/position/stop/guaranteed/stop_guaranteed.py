from binance_f import RequestClient


class StopGuaranteedDto:
    def __init__(self, symbol: str):
        self.symbol: str = symbol


class StopGuaranteed:

    def __init__(self, client: RequestClient, dto: StopGuaranteedDto):
        self.client = client
        self.dto = dto
