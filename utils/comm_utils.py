import random
import string
from typing import List


def random_chars(count: int) -> str:
    letters = string.ascii_letters + string.digits
    oid = (''.join(random.choice(letters) for i in range(count)))
    return oid


def get_order_cid(tags: List[str]) -> str:
    _ts = [t for t in tags]
    _ts.append(random_chars(4))
    _ts.sort()
    shows = '-'.join(_ts)
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


def parse_group_uid_by_tag(tag: str) -> str:
    if not tag.startswith('_G'):
        return None
    if not tag.endswith('_'):
        return list()
    return tag[2:-1]


def parse_group_uid(ss: List[str]) -> str:
    for s in ss:
        uid = parse_group_uid_by_tag(s)
        if uid is not None:
            return uid
    return None


def gen_group_uid() -> str:
    uid = random_chars(3)
    return f'_G{uid}_'
