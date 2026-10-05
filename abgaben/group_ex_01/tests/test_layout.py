import pytest

from perceptual_model.layout import node_anchor

PLAIN = """graph 0.5 10 20
node P 5 19 2 0.5 "" solid box black lightgrey
node eq 8 4 4 1 "" solid none black white
edge P eq 2 5 18 8 4.5 solid black
stop
"""


def test_node_anchor_returns_centre_and_width_as_fractions_of_the_drawing():
    anchor = node_anchor(PLAIN, "eq")
    assert anchor.x == pytest.approx(0.8)
    assert anchor.y == pytest.approx(0.2)
    assert anchor.width == pytest.approx(0.4)


def test_node_anchor_rejects_unknown_node():
    with pytest.raises(KeyError):
        node_anchor(PLAIN, "missing")
