from rest.position.stop import position_stop_utils
from rest.position.stop.position_stop_utils import GuaranteedBundle


def test_calc_guaranteed_long_price():
    i = GuaranteedBundle(
        amount=100,
        price=60,
        lever=50,
        closeRate=0.1
    )
    ans = position_stop_utils.calc_guaranteed_long_price(i)
    print(ans)

def test_calc_guaranteed_short_price():
    i = GuaranteedBundle(
        amount=100,
        price=60,
        lever=50,
        closeRate=0.1
    )
    ans = position_stop_utils.calc_guaranteed_short_price(i)
    print(ans)
