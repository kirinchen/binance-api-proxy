import logging
from datetime import datetime
from typing import Dict, List, Any
import requests
import dateutil.parser

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


class SerialVal:

    def __init__(self, time: str, val: float):
        self.time: datetime = dateutil.parser.parse(time)
        self.val: float = val


class Serial:

    def __init__(self, columns: Dict[str, Any], values: Dict[str, float]):
        self.columns: Dict[str, Any] = columns
        self.values: List[SerialVal] = self._convert_vals(values)

    def _convert_vals(self, values: Dict[str, float]) -> List[SerialVal]:
        ans: List[SerialVal] = list()
        for k, v in values.items():
            ans.append(SerialVal(k, v))


def query(q: str) -> List[Serial]:
    ans: List[Serial] = list()
    fu = config.env('fin-proxy.url')
    qdata = dict()
    qdata['query'] = q
    url = fu + '/proxy/tsdb'
    resp = requests.post(url=url, json=qdata)
    jlist: List[dict] = resp.json()
    for s in jlist:
        ans.append(Serial(**s))
    return ans
