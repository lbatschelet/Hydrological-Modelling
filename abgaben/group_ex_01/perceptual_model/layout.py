"""Read node positions from Graphviz `-Tplain` output."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Anchor:
    """Node centre and width as fractions of the drawing (origin bottom-left)."""

    x: float
    y: float
    width: float


def node_anchor(plain: str, name: str) -> Anchor:
    lines = [line.split() for line in plain.splitlines()]
    _, _, graph_width, graph_height = next(parts for parts in lines if parts[0] == "graph")[:4]
    for parts in lines:
        if parts[0] == "node" and parts[1] == name:
            x, y, width = (float(value) for value in parts[2:5])
            return Anchor(x / float(graph_width), y / float(graph_height), width / float(graph_width))
    raise KeyError(name)
