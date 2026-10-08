from storage import simulate


def test_outflow_uses_storage_from_the_start_of_the_step():
    storage, outflow = simulate([10, 0, 0], k=0.1)
    assert outflow == [0.0, 1.0, 0.9]
    assert storage[0] == 10


def test_second_storage_receives_first_outflow():
    _, outflow_1 = simulate([10, 0, 0], k=0.1)
    _, outflow_2 = simulate(outflow_1, k=0.5)
    assert outflow_2 == [0.0, 0.0, 0.5]
