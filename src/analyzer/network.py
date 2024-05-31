from __future__ import annotations

import math
from typing import Any, Self

from attr import field, frozen
from icecream import ic

from analyzer.IR import (
    ArchitectueConfig,
    NetworkElem,
    StorageAttrtributes,
    WorkloadConfig,
)
from analyzer.tile_analysis import AnalyzeResult
from analyzer.utils import get_logger

logger = get_logger()


@frozen
class ConnectionInfo:
    source: str | set[str]
    sink: str | set[str]
    datawidth: int | None = field(default=None)
    bandwidth: int | None = field(default=None)
    handle_dataspaces: set[str] | None = field(default=None)


class Network:
    def __init__(
        self: Self,
        connection_info: ConnectionInfo,
        hierarchy_level: int,
    ) -> None:
        self.children: list[Network] = []

        self.source = connection_info.source
        self.sink = connection_info.sink
        self.datawidth = connection_info.datawidth
        self.bandwidth = connection_info.bandwidth
        self.hierarchy_level = hierarchy_level
        self.handle_dataspaces = connection_info.handle_dataspaces

        if isinstance(self.source, set):
            self._connections: dict[str, dict[str, Network]] = {
                s: {} for s in self.source
            }

    @classmethod
    def create(
        cls: type[Network],
        network: NetworkElem,
        arch: ArchitectueConfig,
        workload: WorkloadConfig,
    ) -> Network:
        hierarchy_level = cls._get_hierarchy_level(network, arch)

        root_network = cls(
            connection_info=ConnectionInfo(
                source=network.source,
                sink=network.sink,
            ),
            hierarchy_level=hierarchy_level,
        )

        connection_pairs = ((s, t) for s in network.source for t in network.sink - {s})
        for source, sink in connection_pairs:
            root_network._add_child(
                cls(
                    ConnectionInfo(
                        source=source,
                        sink=sink,
                        datawidth=network.attributes.datawidth,
                        bandwidth=cls._get_bandwidth(source, sink, arch),
                        handle_dataspaces=cls._get_handle_dataspaces(
                            source, sink, workload, arch
                        ),
                    ),
                    hierarchy_level=hierarchy_level,
                )
            )
        return root_network

    @staticmethod
    def _get_hierarchy_level(network: NetworkElem, arch: ArchitectueConfig) -> int:
        # Check all sources and sinks are above same container
        lvl = 0
        hierarchy_levels: dict[str, int] = {}
        for elem_name, elem in arch.hierarchy.items():
            hierarchy_levels[elem_name] = lvl
            if elem.elem_type == "container":
                lvl += 1

        source_levels = {hierarchy_levels[s] for s in network.source}
        sink_levels = {hierarchy_levels[s] for s in network.sink}

        if len(source_levels) > 1 or len(sink_levels) > 1:
            err_msg = "Network source and sink must be above the same container"
            raise ValueError(err_msg)

        return source_levels.pop()

    @staticmethod
    def _get_bandwidth(source: str, sink: str, arch: ArchitectueConfig) -> int:
        source_attrs = arch.hierarchy[source].attributes
        sink_attrs = arch.hierarchy[sink].attributes

        if isinstance(source_attrs, StorageAttrtributes):
            read_bandwidth = (
                source_attrs.shared_bandwidth
                if source_attrs.shared_bandwidth
                else source_attrs.read_bandwidth
            )
        else:
            read_bandwidth = math.inf

        if isinstance(sink_attrs, StorageAttrtributes):
            write_bandwidth = (
                sink_attrs.shared_bandwidth
                if sink_attrs.shared_bandwidth
                else sink_attrs.write_bandwidth
            )
        else:
            write_bandwidth = math.inf

        assert read_bandwidth is not None and write_bandwidth is not None
        return int(min(read_bandwidth, write_bandwidth))

    @staticmethod
    def _get_handle_dataspaces(
        source: str, sink: str, workload: WorkloadConfig, arch: ArchitectueConfig
    ) -> set[str]:
        assert source != sink

        for elem_name in arch.hierarchy:
            # If source up to sink, handle readed dataspaces
            if source == elem_name:
                return set(workload.dataspaces_type.keys())
            # If sink up to source, handle writed dataspaces
            elif sink == elem_name:
                return {
                    ds
                    for ds, ds_type in workload.dataspaces_type.items()
                    if ds_type == "write"
                }

        err_msg = "Source and sink not found in hierarchy"
        raise ValueError(err_msg)

    def evaluate_latency(self: Self, result: AnalyzeResult) -> int:
        if not self.children:
            return self._evaluate_latency(result)
        else:
            # TODO: Only consider unicast for now, need to add multicast
            return sum(child.evaluate_latency(result) for child in self.children)

    def _evaluate_latency(self: Self, result: AnalyzeResult) -> int:
        assert self.bandwidth is not None
        assert self.handle_dataspaces is not None
        assert isinstance(self.sink, str)

        tile_accesses = result.tile_accesses.get(self.sink)
        if tile_accesses is None:
            tile_accesses = result.tile_accesses.get(f"{self.sink}_spatial")

        assert tile_accesses is not None
        latency = sum(
            math.ceil(tile_access / self.bandwidth)
            for tile_name, tile_access in tile_accesses.items()
            if tile_name in self.handle_dataspaces
        )

        msg = (
            f"{self.source:<10}-> {self.sink:<10} | "
            f"{latency:<10} cycles | {self.handle_dataspaces}"
        )
        logger.debug(msg)

        return latency

    def _add_child(self: Self, child: Network) -> None:
        assert isinstance(child.source, str) and isinstance(child.sink, str)

        self._connections[child.source] |= {child.sink: child}
        self.children.append(child)
