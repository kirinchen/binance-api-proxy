from utils import comm_utils


def test_calc_proportional_first():
    ans = comm_utils.calc_proportional_first(140, 1.2, 6)
    print(ans)
