from __future__ import annotations

import copy
import gzip
import os
from typing import Any

import orjson
import pytricia

from inc.globals import IPV4_SIZE, IPV6_SIZE


class AsStats:
    asn: int
    v4_pfx_tree: pytricia.PyTricia  # V4 prefixes in a searchable tree
    v6_pfx_tree: pytricia.PyTricia  # V6 prefixes in a searchable tree
    v4_percent: float  # Percent of IPv4 address space seen via AS
    v6_percent: float  # Percent of IPv6 address space seen via AS
    as_path_lengths: dict[
        int, int
    ]  # Frequency of each AS Path length seen (per prefix) keyed by length
    avg_as_path_length: int  # Average AS path length frequency (per prefix)
    weighted_as_path_score: (
        int  # Weighted score of AS path length frequencies (per prefix)
    )
    as_hops: dict[
        int, set[int]
    ]  # How many hops to each ASN (dict value) keyed by hop count
    as_hops_freq: dict[
        int, int
    ]  # Frequency of AS hop counts, keyed by hop count
    avg_as_hops: int  # Average of AS hop count frequency
    weighted_as_hops_score: int  # Weighted score of AS hop counts
    peers_w_cover_v4_pfx: dict[int, int]
    peers_wo_cover_v4_pfx: dict[int, int]
    v4_pfx_covered_by_peers: set[
        str
    ]  # v4 prefixes which other networks also have in their table
    v4_pfx_n_covered_by_peers: set[
        str
    ]  # v4 prefixes not visible by any other network
    v4_pfx_preferred_by_t1s: set[
        str
    ]  # v4 prefixes with shortest AS path via Tier 1(s)
    v4_pfx_n_preferred_by_t1s: set[str]  # v4 prefixes not going via Tier 1(s)
    peers_w_cover_v6_pfx: dict[int, int]
    peers_wo_cover_v6_pfx: dict[int, int]
    v6_pfx_covered_by_peers: set[
        str
    ]  # v6 prefixes which other networks also have in their table
    v6_pfx_n_covered_by_peers: set[
        str
    ]  # v6 prefixes not visible by any other network
    v6_pfx_preferred_by_t1s: set[
        str
    ]  # v6 prefixes with shortest AS path via Tier 1(s)
    v6_pfx_n_preferred_by_t1s: set[str]  # v4 prefixes not going via Tier 1(s)
    asns_reachable: set[
        int
    ]  # All ASNs this network can reach via any peer (the AS cone)
    asns_reachable_via_peers: set[
        int
    ]  # ASNs which are reachable via other networks
    asns_n_reachable_via_peers: set[
        int
    ]  # ASNs which are not reachable via other networks
    peers_w_reachable_asn: dict[
        int, int
    ]  # Count per peer of how many overlapping reachable ASNs the local ASN has with the peer ASN
    peers_wo_reachable_asn: dict[
        int, int
    ]  # Count per peer of how many reachable ASNs the local ASN has which the peer can not reach
    on_net_asns: set[int]  # On-net ASNs (direct peers)
    asns_on_net_for_peers: set[int]  # On-net ASNs also reachable via peers
    asns_n_on_net_for_peers: set[int]  # On-net ASNs not reachable via peers
    peers_w_asn_on_net: dict[
        int, int
    ]  # Count per peer of how many overlapping on-net ASNs the local ASN has with the peer ASN
    peers_wo_asn_on_net: dict[
        int, int
    ]  # Count per peer of how many on-net ASNs the local ASN has which the peer does not have on-net

    def __init__(
        self: AsStats,
        asn: int = -1,
        v4_percent: float = 0.0,
        v6_percent: float = 0.0,
        v4_pfx_tree: pytricia.PyTricia = pytricia.PyTricia(IPV4_SIZE),
        v6_pfx_tree: pytricia.PyTricia = pytricia.PyTricia(IPV6_SIZE),
        as_path_lengths: dict[int, int] = {},
        avg_as_path_length: int = 0,
        weighted_as_path_score: int = 0,
        as_hops: dict[int, set[int]] = {},
        as_hops_freq: dict[int, int] = {},
        avg_as_hops: int = 0,
        weighted_as_hops_score: int = 0,
        peers_w_cover_v4_pfx: dict[int, int] = {},
        peers_wo_cover_v4_pfx: dict[int, int] = {},
        v4_pfx_covered_by_peers: set[str] = set(),
        v4_pfx_n_covered_by_peers: set[str] = set(),
        v4_pfx_preferred_by_t1s: set[str] = set(),
        v4_pfx_n_preferred_by_t1s: set[str] = set(),
        peers_w_cover_v6_pfx: dict[int, int] = {},
        peers_wo_cover_v6_pfx: dict[int, int] = {},
        v6_pfx_covered_by_peers: set[str] = set(),
        v6_pfx_n_covered_by_peers: set[str] = set(),
        v6_pfx_preferred_by_t1s: set[str] = set(),
        v6_pfx_n_preferred_by_t1s: set[str] = set(),
        asns_reachable: set[int] = set(),
        asns_reachable_via_peers: set[int] = set(),
        asns_n_reachable_via_peers: set[int] = set(),
        peers_w_reachable_asn: dict[int, int] = {},
        peers_wo_reachable_asn: dict[int, int] = {},
        on_net_asns: set[int] = set(),
        asns_on_net_for_peers: set[int] = set(),
        asns_n_on_net_for_peers: set[int] = set(),
        peers_w_asn_on_net: dict[int, int] = {},
        peers_wo_asn_on_net: dict[int, int] = {},
    ) -> None:
        self.asn = asn
        self.v4_percent = v4_percent
        self.v6_percent = v6_percent
        self.v4_pfx_tree = v4_pfx_tree
        self.v6_pfx_tree = v6_pfx_tree
        self.as_path_lengths = as_path_lengths
        self.avg_as_path_length = avg_as_path_length
        self.weighted_as_path_score = weighted_as_path_score
        self.as_hops = as_hops
        self.as_hops_freq = as_hops_freq
        self.avg_as_hops = avg_as_hops
        self.weighted_as_hops_score = weighted_as_hops_score
        self.peers_w_cover_v4_pfx = peers_w_cover_v4_pfx
        self.peers_wo_cover_v4_pfx = peers_wo_cover_v4_pfx
        self.v4_pfx_covered_by_peers = v4_pfx_covered_by_peers
        self.v4_pfx_n_covered_by_peers = v4_pfx_n_covered_by_peers
        self.v4_pfx_preferred_by_t1s = v4_pfx_preferred_by_t1s
        self.v4_pfx_n_preferred_by_t1s = v4_pfx_n_preferred_by_t1s
        self.peers_w_cover_v6_pfx = peers_w_cover_v6_pfx
        self.peers_wo_cover_v6_pfx = peers_wo_cover_v6_pfx
        self.v6_pfx_covered_by_peers = v6_pfx_covered_by_peers
        self.v6_pfx_n_covered_by_peers = v6_pfx_n_covered_by_peers
        self.v6_pfx_preferred_by_t1s = v6_pfx_preferred_by_t1s
        self.v6_pfx_n_preferred_by_t1s = v6_pfx_n_preferred_by_t1s
        self.asns_reachable = asns_reachable
        self.asns_reachable_via_peers = asns_reachable_via_peers
        self.asns_n_reachable_via_peers = asns_n_reachable_via_peers
        self.peers_w_reachable_asn = peers_w_reachable_asn
        self.peers_wo_reachable_asn = peers_wo_reachable_asn
        self.on_net_asns = on_net_asns
        self.asns_on_net_for_peers = asns_on_net_for_peers
        self.asns_n_on_net_for_peers = asns_n_on_net_for_peers
        self.peers_w_asn_on_net = peers_w_asn_on_net
        self.peers_wo_asn_on_net = peers_wo_asn_on_net

    @staticmethod
    def from_dict(data: dict[str, Any]) -> AsStats:
        """
        Return an AsnRoutes object from a dict.
        Ensure that dict keys which needs to be int, are int. In the case
        they were read from JSON, they will be string.
        """
        as_stats = AsStats(
            asn=data["asn"],
            v4_percent=data["v4_percent"],
            v6_percent=data["v6_percent"],
            v4_pfx_tree=pytricia.PyTricia(IPV4_SIZE),
            v6_pfx_tree=pytricia.PyTricia(IPV6_SIZE),
            as_path_lengths={
                int(key): value
                for key, value in data["as_path_lengths"].items()
            },
            avg_as_path_length=data["avg_as_path_length"],
            weighted_as_path_score=data["weighted_as_path_score"],
            as_hops={
                int(key): value for key, value in data["as_hops"].items()
            },
            as_hops_freq={
                int(key): value for key, value in data["as_hops_freq"].items()
            },
            avg_as_hops=data["avg_as_hops"],
            weighted_as_hops_score=data["weighted_as_hops_score"],
            peers_w_cover_v4_pfx={
                int(key): value
                for key, value in data["peers_w_cover_v4_pfx"].items()
            },
            peers_wo_cover_v4_pfx={
                int(key): value
                for key, value in data["peers_wo_cover_v4_pfx"].items()
            },
            v4_pfx_covered_by_peers=set(data["v4_pfx_covered_by_peers"]),
            v4_pfx_n_covered_by_peers=set(data["v4_pfx_n_covered_by_peers"]),
            v4_pfx_preferred_by_t1s=set(data["v4_pfx_preferred_by_t1s"]),
            v4_pfx_n_preferred_by_t1s=set(data["v4_pfx_n_preferred_by_t1s"]),
            peers_w_cover_v6_pfx={
                int(key): value
                for key, value in data["peers_w_cover_v6_pfx"].items()
            },
            peers_wo_cover_v6_pfx={
                int(key): value
                for key, value in data["peers_wo_cover_v6_pfx"].items()
            },
            v6_pfx_covered_by_peers=set(data["v6_pfx_covered_by_peers"]),
            v6_pfx_n_covered_by_peers=set(data["v6_pfx_n_covered_by_peers"]),
            v6_pfx_preferred_by_t1s=set(data["v6_pfx_preferred_by_t1s"]),
            v6_pfx_n_preferred_by_t1s=set(data["v6_pfx_n_preferred_by_t1s"]),
            asns_reachable=set(data["asns_reachable"]),
            asns_reachable_via_peers=set(data["asns_reachable_via_peers"]),
            asns_n_reachable_via_peers=set(data["asns_n_reachable_via_peers"]),
            peers_w_reachable_asn={
                int(key): value
                for key, value in data["peers_w_reachable_asn"].items()
            },
            peers_wo_reachable_asn={
                int(key): value
                for key, value in data["peers_wo_reachable_asn"].items()
            },
            on_net_asns=set(data["on_net_asns"]),
            asns_on_net_for_peers=set(data["asns_on_net_for_peers"]),
            asns_n_on_net_for_peers=set(data["asns_n_on_net_for_peers"]),
            peers_w_asn_on_net={
                int(key): value
                for key, value in data["peers_w_asn_on_net"].items()
            },
            peers_wo_asn_on_net={
                int(key): value
                for key, value in data["peers_wo_asn_on_net"].items()
            },
        )

        for prefix in data["v4_pfx_tree"]:
            as_stats.v4_pfx_tree.insert(prefix, None)
        for prefix in data["v6_pfx_tree"]:
            as_stats.v6_pfx_tree.insert(prefix, None)
        return as_stats

    @staticmethod
    def from_json(uncompressed: bool, filename: str) -> AsStats:
        """
        Read an AsStats object from disk, which has been serialised as JSON.
        This may have been optionally GZIP compressed
        """
        if not os.path.exists(filename):
            raise FileExistsError(f"AsStats file doesn't exist: {filename}")

        print(f"{os.getpid()}: Reading {filename}")
        if uncompressed:
            with open(filename) as f:
                return AsStats.from_dict(orjson.loads(f.read()))
        else:
            with gzip.open(filename, "rt") as f:
                return AsStats.from_dict(orjson.loads(f.read()))

    def to_dict(self: AsStats) -> dict[str, Any]:
        """
        In case the dict is being serialised to JSON, we need to ensure all
        dict keys are strings because JSON objects must have string keys.
        """
        return {
            "asn": self.asn,
            "v4_percent": self.v4_percent,
            "v6_percent": self.v6_percent,
            "v4_pfx_tree": list(self.v4_pfx_tree),
            "v6_pfx_tree": list(self.v6_pfx_tree),
            "as_path_lengths": {
                str(key): value for key, value in self.as_path_lengths.items()
            },
            "avg_as_path_length": self.avg_as_path_length,
            "weighted_as_path_score": self.weighted_as_path_score,
            "as_hops": {
                str(key): list(value) for key, value in self.as_hops.items()
            },
            "as_hops_freq": {
                str(key): value for key, value in self.as_hops_freq.items()
            },
            "avg_as_hops": self.avg_as_hops,
            "weighted_as_hops_score": self.weighted_as_hops_score,
            "peers_w_cover_v4_pfx": {
                str(key): value
                for key, value in self.peers_w_cover_v4_pfx.items()
            },
            "peers_wo_cover_v4_pfx": {
                str(key): value
                for key, value in self.peers_wo_cover_v4_pfx.items()
            },
            "v4_pfx_covered_by_peers": list(self.v4_pfx_covered_by_peers),
            "v4_pfx_n_covered_by_peers": list(self.v4_pfx_n_covered_by_peers),
            "v4_pfx_preferred_by_t1s": list(self.v4_pfx_preferred_by_t1s),
            "v4_pfx_n_preferred_by_t1s": list(self.v4_pfx_n_preferred_by_t1s),
            "peers_w_cover_v6_pfx": {
                str(key): value
                for key, value in self.peers_w_cover_v6_pfx.items()
            },
            "peers_wo_cover_v6_pfx": {
                str(key): value
                for key, value in self.peers_wo_cover_v6_pfx.items()
            },
            "v6_pfx_covered_by_peers": list(self.v6_pfx_covered_by_peers),
            "v6_pfx_n_covered_by_peers": list(self.v6_pfx_n_covered_by_peers),
            "v6_pfx_preferred_by_t1s": list(self.v6_pfx_preferred_by_t1s),
            "v6_pfx_n_preferred_by_t1s": list(self.v6_pfx_n_preferred_by_t1s),
            "asns_reachable": list(self.asns_reachable),
            "asns_reachable_via_peers": list(self.asns_reachable_via_peers),
            "asns_n_reachable_via_peers": list(
                self.asns_n_reachable_via_peers
            ),
            "peers_w_reachable_asn": {
                str(key): value
                for key, value in self.peers_w_reachable_asn.items()
            },
            "peers_wo_reachable_asn": {
                str(key): value
                for key, value in self.peers_wo_reachable_asn.items()
            },
            "on_net_asns": list(self.on_net_asns),
            "asns_on_net_for_peers": list(self.asns_on_net_for_peers),
            "asns_n_on_net_for_peers": list(self.asns_n_on_net_for_peers),
            "peers_w_asn_on_net": {
                str(key): value
                for key, value in self.peers_w_asn_on_net.items()
            },
            "peers_wo_asn_on_net": {
                str(key): value
                for key, value in self.peers_wo_asn_on_net.items()
            },
        }

    def to_json(self: AsStats, uncompressed: bool, filename: str) -> None:
        """
        Write an AsStats object to disk serialised as JSON.
        This can optionally be GZIP compressed.
        """
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if uncompressed:
            with open(filename, "wb") as f:
                f.write(
                    orjson.dumps(self.to_dict(), option=orjson.OPT_INDENT_2)
                )
        else:
            with gzip.open(filename, "wb") as f:
                f.write(
                    orjson.dumps(self.to_dict(), option=orjson.OPT_INDENT_2)
                )
        print(f"{os.getpid()}: Wrote to {filename}")


class AsnRoutes:
    """
    Store data for a single ASN, found when parsing RIB data
    """

    peer_as: int
    v4_count: int
    v6_count: int
    routes: dict[str, list[list[int]]]

    def __init__(
        self: AsnRoutes,
        peer_as: int = -1,
        v4_count: int = 0,
        v6_count: int = 0,
        routes: dict[str, list[list[int]]] = {},
    ) -> None:
        self.peer_as = peer_as
        self.v4_count = v4_count
        self.v6_count = v6_count
        self.routes = routes

    def __repr__(self: AsnRoutes) -> str:
        stats = f"peer_as: {self.peer_as}\n"
        stats += f"v4_count: {self.v4_count}\n"
        stats += f"v6_count: {self.v6_count}\n"
        stats += f"routes_count: {len(self.routes)}\n"
        return stats

    def add_prefix(self: AsnRoutes, prefix: str, as_path: list[int]) -> None:
        """
        Add a prefix if it is missing, and the AS path if it is new
        """
        if prefix not in self.routes:
            self.routes[prefix] = []
            if ":" in prefix:
                self.v6_count += 1
            else:
                self.v4_count += 1

        if as_path not in self.routes[prefix]:
            self.routes[prefix].append(as_path)

    def copy(self: AsnRoutes) -> AsnRoutes:
        """
        Return a copy of this object
        """
        return AsnRoutes(
            peer_as=self.peer_as,
            v4_count=self.v4_count,
            v6_count=self.v6_count,
            routes=copy.deepcopy(self.routes),
        )

    @staticmethod
    def from_dict(data: dict[str, Any]) -> AsnRoutes:
        """
        Return an AsnRoutes object from a dict
        """
        return AsnRoutes(
            peer_as=int(data["peer_as"]),
            v4_count=int(data["v4_count"]),
            v6_count=int(data["v6_count"]),
            routes=data["routes"],
        )

    def merge_asn_routes(self: AsnRoutes, asn_routes: AsnRoutes) -> None:
        """
        Merge another AsnRoutes object into this one
        """
        for prefix, as_paths in asn_routes.routes.items():
            if prefix == "":
                raise ValueError(
                    f"AS{self.peer_as} has empty prefix with AS-paths: {as_paths}"
                )
            if not as_paths:
                raise ValueError(
                    f"AS{self.peer_as} has prefix {prefix} with no AS path(s)"
                )
            for as_path in as_paths:
                self.add_prefix(prefix, as_path)

    def to_dict(self: AsnRoutes) -> dict[str, Any]:
        return {
            "peer_as": self.peer_as,
            "v4_count": self.v4_count,
            "v6_count": self.v6_count,
            "routes": self.routes,
        }

    def to_json(self: AsnRoutes, uncompressed: bool, filename: str) -> None:
        """
        Write an AsnRoutes object to disk, serialised as JSON.
        This can optionally be gzip compressed.
        """
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        if uncompressed:
            with open(filename, "wb") as f:
                f.write(
                    orjson.dumps(self.to_dict(), option=orjson.OPT_INDENT_2)
                )
        else:
            with gzip.open(filename, "wb") as f:
                f.write(
                    orjson.dumps(self.to_dict(), option=orjson.OPT_INDENT_2)
                )
        # print(f"{os.getpid()}: Wrote to {filename}")


class PeerStats:
    peer_type: int
    peer_bgp_id: str
    peer_ip: str
    peer_as: int
    peer_index: int
    v4_count: int = 0
    v6_count: int = 0
    routes: dict[str, list[int]] = {}

    def __init__(
        self: PeerStats,
        peer_type: int,
        peer_bgp_id: str,
        peer_ip: str,
        peer_as: int,
        peer_index: int,
        v4_count: int = 0,
        v6_count: int = 0,
        routes: dict[str, list[int]] = {},
    ) -> None:
        self.peer_type = peer_type
        self.peer_bgp_id = peer_bgp_id
        self.peer_ip = peer_ip
        self.peer_as = peer_as
        self.peer_index = peer_index
        self.v4_count = v4_count
        self.v6_count = v6_count
        self.routes = routes

    def __repr__(self: PeerStats) -> str:
        stats = f"peer_type: {self.peer_type}\n"
        stats += f"peer_bgp_id: {self.peer_bgp_id}\n"
        stats += f"peer_ip: {self.peer_ip}\n"
        stats += f"peer_as: {self.peer_as}\n"
        stats += f"peer_index: {self.peer_index}\n"
        stats += f"v4_count: {self.v4_count}\n"
        stats += f"v6_count: {self.v6_count}\n"
        stats += f"routes_count: {len(self.routes)}\n"
        return stats

    def to_dict(self: PeerStats) -> dict[str, Any]:
        return {
            "peer_type": self.peer_type,
            "peer_bgp_id": self.peer_bgp_id,
            "peer_ip": self.peer_ip,
            "peer_as": self.peer_as,
            "peer_index": self.peer_index,
            "v4_count": self.v4_count,
            "v6_count": self.v6_count,
            "routes": self.routes,
        }
