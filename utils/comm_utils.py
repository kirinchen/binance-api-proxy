import random
import string
from enum import Enum
from typing import List, Any, TypeVar


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


E = TypeVar('E', bound=Enum)


def value_of_enum(e: E, v: Any) -> E:
    for _e in e:
        e: E = _e
        if e.value == v:
            return e
    raise KeyError('Not find :' + v)


def fix_precision(p: int, fv: float):
    fstr = str(p) + 'f'
    ans = float(('{:.' + fstr + '}').format(fv))
    return str(ans)


def to_dict(obj, classkey=None) -> dict:
    if isinstance(obj, dict):
        data = {}
        for (k, v) in obj.items():
            data[k] = to_dict(v, classkey)
        return data
    elif hasattr(obj, "_ast"):
        return to_dict(obj._ast())
    elif hasattr(obj, "__iter__") and not isinstance(obj, str):
        return [to_dict(v, classkey) for v in obj]
    elif hasattr(obj, "__dict__"):
        data = dict([(key, to_dict(value, classkey))
                     for key, value in obj.__dict__.items()
                     if not callable(value) and not key.startswith('_')])
        if classkey is not None and hasattr(obj, "__class__"):
            data[classkey] = obj.__class__.__name__
        return data
    else:
        return obj


def calc_proportional_first(sum: float, rate: float, n: int) -> float:
    sun = sum * (1 - rate)
    mom = 1 - pow(rate, n)
    return sun / mom
