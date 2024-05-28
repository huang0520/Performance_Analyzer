from __future__ import annotations

from typing import Any, Self


class Network:
    def __init__(self: Self) -> None:
        self.children: list[Network] = []

    def evaluate_latency(self: Self) -> int:
        if not self.children:
            pass
        else:
            pass

    def add_child(self: Self, child: Network) -> None:
        self.children.append(child)


class ConnectionTable(dict[str, dict[str, Network]]):
    def get_network(self: Self, source: str, sink: str) -> Network:
        return self[source][sink]
