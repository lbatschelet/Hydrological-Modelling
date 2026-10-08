from storage import cascade, max_discharge_grid


def test_second_storage_receives_first_outflow_not_precipitation():
    _, outflow_2 = cascade([10, 0, 0], k1=0.1, k2=0.5)
    assert outflow_2 == [0.0, 0.0, 0.5]


def test_cascade_keeps_draining_after_precipitation_stops():
    _, outflow_2 = cascade([10, 0, 0, 0], k1=0.1, k2=0.1)
    assert len(outflow_2) == 4
    assert max(outflow_2) > 0


def test_max_discharge_covers_all_nine_k_pairs():
    inflow = [10] * 10 + [0] * 60
    rows = max_discharge_grid(inflow, [0.1, 0.4, 0.7])
    pairs = {(k1, k2) for k1, k2, _max_q in rows}
    assert pairs == {(a, b) for a in (0.1, 0.4, 0.7) for b in (0.1, 0.4, 0.7)}
    assert all(max_q > 0 for _k1, _k2, max_q in rows)
