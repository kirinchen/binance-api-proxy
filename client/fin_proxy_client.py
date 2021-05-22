import logging
from datetime import datetime
from typing import Dict, List
import requests

import config


class PointDto:

    def __init__(self, measurement: str, tags: Dict[str, str], field: str, val: float, time: datetime):
        self.measurement = measurement
        self.tags = tags
        self.field = field
        self.val = val
        self.time = time.isoformat()


def post_multiple(dtos: List[PointDto]):
    fu = config.env('fin-proxy.url')
    url = fu + '/proxy/tsdb/insert/multiple'
    jl = [j.__dict__ for j in dtos]
    resp = requests.post(url=url, json=jl)
    logging.warning(resp.text)
