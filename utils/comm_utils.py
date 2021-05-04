import random
import string
from typing import List


def random_chars(count: int) -> str:
    letters = string.ascii_letters
    oid = (''.join(random.choice(letters) for i in range(count)))
    return oid


def get_order_cid(tags: List[str]) -> str:
    tags.sort()
    shows = '-'.join(tags)
    return '_' + shows + '_'


def to_struct_list(rs: List[object]) -> List[dict]:
    pos = [r.__dict__ for r in rs]
    return pos


def contains_tags(cid: str, trytags: List[str]) -> bool:
    otags = parse_tags(cid)
    for tg in trytags:
        if tg in otags:
            return True
    return False


def parse_tags(cid: str) -> List[str]:
    if not cid.startswith('_'):
        return list()
    if not cid.endswith('_'):
        return list()
    cid = cid[1:-1]
    return cid.split('-')
