import random
import string


def random_chars(count:int)->str:
    letters = string.ascii_letters
    oid = (''.join(random.choice(letters) for i in range(count)))
    return oid