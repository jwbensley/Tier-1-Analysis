#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import gc
import gzip
import json
import multiprocessing
import os
from typing import Optional, Union

import orjson
import pytricia
from inc.aggregate6 import aggregate_pyt
from inc.asns import asns, is_tier1, skip_asn
from inc.bogon_asns import BogonAsns
from inc.bogon_prefixes import BogonPrefixes
from inc.countries import get_asn_to_continent_mappings
from inc.globals import (
    COVERAGE_AS_CONE,
    COVERAGE_AS_HOP_COUNT_ASNS,
    COVERAGE_AS_HOP_COUNT_PREFIXES,
    COVERAGE_CONTINENT_BREAKDOWN,
    COVERAGE_DATA_PATH,
    COVERAGE_GLOBAL,
    COVERAGE_IP,
    COVERAGE_PEERING,
    COVERAGE_PEERINGS,
    COVERAGE_V4,
    COVERAGE_V4_SHORTER_T1,
    COVERAGE_V6,
    COVERAGE_V6_SHORTER_T1,
    FULL_TABLE_REPORT,
    IPV4_SIZE,
    IPV6_SIZE,
    MERGED_PATHS_PATH,
    NRO_ALLOCATIONS,
    RAW_DATA,
)
from inc.stats import AsnRoutes, AsStats
from tabulate import tabulate


class GlobalStats:
    all_asns: set[int] = set()  # All unique ASNs seen via all networks
    v4_pfx_tree: pytricia.PyTricia = pytricia.PyTricia(
        IPV4_SIZE
    )  # All unique v4 prefixes seen via all networks
    v4_ips = 0  # Total number of IP addresses covered by all seen prefixes
    v6_pfx_tree: pytricia.PyTricia = pytricia.PyTricia(
        IPV6_SIZE
    )  # All unique v6 prefixes seen via all networks
    v6_ips = 0  # Total number of IP addresses covered by all seen prefixes

    @classmethod
    def to_dict(cls) -> dict[str, Union[list[Union[int, str]], int]]:
        return {
            "all_asns": list(GlobalStats.all_asns),
            "v4_pfx_tree": list(GlobalStats.v4_pfx_tree),
            "v4_ips": GlobalStats.v4_ips,
            "v6_pfx_tree": list(GlobalStats.v6_pfx_tree),
            "v6_ips": GlobalStats.v6_ips,
        }

    @classmethod
    def to_json(cls) -> None:
        filename = os.path.join(cli_args.output, COVERAGE_GLOBAL)
        with gzip.open(filename, "wb") as f:
            # Orjson can't dump >64bit int (GlobalStats.v6_ips)
            f.write(json.dumps(GlobalStats.to_dict(), indent=2).encode())
        print(f"Wrote global stats to {filename}")


class IpCoverage:
    asn: int
    v4_percent: float
    v6_percent: float

    def __init__(
        self: IpCoverage, asn: int, v4_percent: float, v6_percent: float
    ) -> None:
        self.asn = asn
        self.v4_percent = v4_percent
        self.v6_percent = v6_percent


cli_args: argparse.Namespace


def get_asn_report() -> dict[str, dict[str, Union[int, bool]]]:
    assert os.path.exists(cli_args.report)
    with open(cli_args.report) as f:
        data = orjson.loads(f.read())
        assert isinstance(data, dict)  # mypy
        return data


def get_asns_full_table_asn() -> list[int]:
    """
    Return a list of ASNs which, according to the full table report,
    have True stored under the ASN threshold.
    """
    asn_data = get_asn_report()
    asn_list = []
    for asn in asn_data:
        if asn_data[asn]["asn_full"]:
            asn_list.append(int(asn))
    return asn_list


def get_asns_full_table_ip() -> list[int]:
    """
    Return a list of ASNs which, according to the full table report,
    have True stored under the IP thresholds.
    """
    asn_data = get_asn_report()
    asn_list = []
    for asn in asn_data:
        if asn_data[asn]["v4_full"] or asn_data[asn]["v6_full"]:
            asn_list.append(int(asn))
    return asn_list


def get_asns_full_table_any() -> list[int]:
    """
    Return a list of ASNs which, according to the full table report,
    have True stored under any threshold.
    """
    asn_data = get_asn_report()
    asn_list = []
    for asn in asn_data:
        if (
            asn_data[asn]["v4_full"]
            or asn_data[asn]["v6_full"]
            or asn_data[asn]["asn_full"]
        ):
            asn_list.append(int(asn))
    return asn_list


def get_input_filenames(asn_list: list[int], compressed: bool) -> list[str]:
    """
    Return a list of AsnRoutes JSON filenames based on the chosen ASNs
    """
    filenames: list[str] = []
    for asn in asn_list:
        filename = os.path.join(cli_args.input, f"{asn}-routes.json")
        if compressed:
            filename += ".gz"
        if not os.path.exists(filename):
            raise FileExistsError(f"Input file doesn't exist: {filename}")
        filenames.append(filename)
    return filenames


def get_output_filename(prefix: str, compressed: bool, output_dir: str) -> str:
    """
    Return output filename for serialising AsStats objects to JSON
    """
    filename = os.path.join(output_dir, f"{prefix}-stats.json")
    if compressed:
        return filename + ".gz"
    return filename


def get_output_filenames(
    asn_list: list[int], compressed: bool, output_dir: str
) -> list[str]:
    """
    Return the list of parsed AsStat filenames based on the chosen ASNs
    """
    filenames: list[str] = []
    for asn in asn_list:
        filename = get_output_filename(str(asn), compressed, output_dir)
        if not os.path.exists(filename):
            raise FileExistsError(f"Parsed file doesn't exist: {filename}")
        filenames.append(filename)
    return filenames


def calculate_asn_coverage(as_stats_files: list[str]) -> None:
    """
    Calculate ASN coverage and reachability stats
    """

    print(f"Calculating ASN coverage for {len(as_stats_files)} networks")

    # Can't call from_json with multiprocessing, pytri can't be pickled
    all_as_stats: list[AsStats] = []
    for as_stats_file in as_stats_files:
        all_as_stats.append(
            AsStats.from_json(cli_args.uncompressed, as_stats_file)
        )

    for as_stats in all_as_stats:
        GlobalStats.all_asns.update(as_stats.asns_reachable)

    for local_as in all_as_stats:
        print(f"Comparing ASNs for {local_as.asn}")

        # Find the ASNs reachable by each network either on- or off-net
        for peer_as in all_as_stats:
            if local_as == peer_as:
                continue

            local_as.peers_w_asn_on_net[peer_as.asn] = 0
            local_as.peers_wo_asn_on_net[peer_as.asn] = 0
            local_as.peers_w_reachable_asn[peer_as.asn] = 0
            local_as.peers_wo_reachable_asn[peer_as.asn] = 0

            for on_net_asn in local_as.on_net_asns:
                if on_net_asn in peer_as.on_net_asns:
                    local_as.peers_w_asn_on_net[peer_as.asn] += 1
                    local_as.asns_on_net_for_peers.add(on_net_asn)
                    if on_net_asn in local_as.asns_n_on_net_for_peers:
                        local_as.asns_n_on_net_for_peers.remove(on_net_asn)
                else:
                    local_as.peers_wo_asn_on_net[peer_as.asn] += 1

            for reachable_asn in local_as.asns_reachable:
                if reachable_asn in peer_as.asns_reachable:
                    local_as.peers_w_reachable_asn[peer_as.asn] += 1
                    local_as.asns_reachable_via_peers.add(reachable_asn)
                    if reachable_asn in local_as.asns_n_reachable_via_peers:
                        local_as.asns_n_reachable_via_peers.remove(
                            reachable_asn
                        )
                else:
                    local_as.peers_wo_reachable_asn[peer_as.asn] += 1

        local_as.to_json(
            cli_args.uncompressed,
            get_output_filename(str(local_as.asn), True, cli_args.output),
        )

    print("")
    print(f"ASNs Found via All Peers: {len(GlobalStats.all_asns)}")
    print("")
    print_as_cone_coverage(all_as_stats)
    print_as_hops(all_as_stats)
    print_as_path_length(all_as_stats)
    print_continent_breakdown(all_as_stats)
    print_peer_coverage(all_as_stats)
    print_peerings(all_as_stats)


def calculate_global_prefixes(as_stats_files: list[str]) -> None:
    """
    Populate the prefix trees for all unique routes see across all networks
    """

    print(
        f"Calculating global prefixes seen via {len(as_stats_files)} networks"
    )
    for as_stats_file in as_stats_files:
        as_stats = AsStats.from_json(cli_args.uncompressed, as_stats_file)
        # Update the global stats for prefixes seen via a network
        for prefix in as_stats.v4_pfx_tree:
            GlobalStats.v4_pfx_tree.insert(prefix, None)
        for prefix in as_stats.v6_pfx_tree:
            GlobalStats.v6_pfx_tree.insert(prefix, None)

    v4_aggregates = aggregate_pyt(GlobalStats.v4_pfx_tree, IPV4_SIZE)
    v6_aggregates = aggregate_pyt(GlobalStats.v6_pfx_tree, IPV6_SIZE)

    for prefix in v4_aggregates:
        mask = int(prefix.split("/")[1])
        GlobalStats.v4_ips += 2 ** (IPV4_SIZE - mask)

    for prefix in v6_aggregates:
        mask = int(prefix.split("/")[1])
        GlobalStats.v6_ips += 2 ** (IPV6_SIZE - mask)

    print(
        f"{len(GlobalStats.v4_pfx_tree)} v4 prefixes seen across all networks"
    )
    print(f"{len(v4_aggregates)} v4 prefixes after aggregation")
    print(f"{GlobalStats.v4_ips} IPv4 addresses covered by v4 prefixes")
    print(
        f"{len(GlobalStats.v6_pfx_tree)} v6 prefixes seen across all networks"
    )
    print(f"{len(v4_aggregates)} v6 prefixes after aggregation")
    print(f"{GlobalStats.v6_ips} IPv6 addresses covered by v6 prefixes")
    print("")


def calculate_ip_coverage_per_asn(filename: str) -> IpCoverage:
    """
    Calculate the coverage of IP space visible via a network
    """
    as_stats = AsStats.from_json(cli_args.uncompressed, filename)

    print(f"{os.getpid()}: Calculating IP coverage for {as_stats.asn}")
    result = IpCoverage(as_stats.asn, 0, 0)

    v4_aggregates = aggregate_pyt(as_stats.v4_pfx_tree, IPV4_SIZE)
    v4_ips = 0
    for prefix in v4_aggregates:
        mask = int(prefix.split("/")[1])
        v4_ips += 2 ** (IPV4_SIZE - mask)
    as_stats.v4_percent = (v4_ips / GlobalStats.v4_ips) * 100
    result.v4_percent = as_stats.v4_percent

    v6_ips = 0
    v6_aggregates = aggregate_pyt(as_stats.v6_pfx_tree, IPV6_SIZE)
    for prefix in v6_aggregates:
        mask = int(prefix.split("/")[1])
        v6_ips += 2 ** (IPV6_SIZE - mask)
    as_stats.v6_percent = (v6_ips / GlobalStats.v6_ips) * 100
    result.v6_percent = as_stats.v6_percent

    as_stats.to_json(
        cli_args.uncompressed,
        get_output_filename(str(as_stats.asn), True, cli_args.output),
    )

    return result


def calculate_ip_coverage(as_stats_files: list[str]) -> None:
    """
    Calculate the percentage of IP space visible via all networks
    """

    print(f"Calculating IP coverage for {len(as_stats_files)} networks")

    if not len(GlobalStats.v4_pfx_tree) or not len(GlobalStats.v6_pfx_tree):
        calculate_global_prefixes(as_stats_files=as_stats_files)
        gc.collect()

    pool = multiprocessing.Pool(cli_args.p)
    results: list[IpCoverage] = pool.map(
        calculate_ip_coverage_per_asn, as_stats_files
    )
    pool.close()
    print("")

    print_ip_coverage(results)


def calculate_prefix_coverage(as_stats_files: list[str]) -> None:
    """
    Find all the unique and overlapping prefixes between ASNs
    """

    print(f"Calculating prefix coverage for {len(as_stats_files)} networks")

    # Can't call from_json with multiprocessing, pytri can't be pickled
    all_as_stats: list[AsStats] = []
    for as_stats_file in as_stats_files:
        all_as_stats.append(
            AsStats.from_json(cli_args.uncompressed, as_stats_file)
        )

    for local_as in all_as_stats:
        print(f"Comparing prefixes for {local_as.asn}")
        for peer_as in all_as_stats:

            if local_as == peer_as:
                continue

            local_as.peers_w_cover_v4_pfx[peer_as.asn] = 0
            local_as.peers_wo_cover_v4_pfx[peer_as.asn] = 0
            local_as.peers_w_cover_v6_pfx[peer_as.asn] = 0
            local_as.peers_wo_cover_v6_pfx[peer_as.asn] = 0

            for prefix in local_as.v4_pfx_tree:
                if prefix in peer_as.v4_pfx_tree:
                    local_as.peers_w_cover_v4_pfx[peer_as.asn] += 1
                    local_as.v4_pfx_covered_by_peers.add(prefix)
                    if prefix in local_as.v4_pfx_n_covered_by_peers:
                        local_as.v4_pfx_n_covered_by_peers.remove(prefix)
                else:
                    local_as.peers_wo_cover_v4_pfx[peer_as.asn] += 1

            for prefix in local_as.v6_pfx_tree:
                if prefix in peer_as.v6_pfx_tree:
                    local_as.peers_w_cover_v6_pfx[peer_as.asn] += 1
                    local_as.v6_pfx_covered_by_peers.add(prefix)
                    if prefix in local_as.v6_pfx_n_covered_by_peers:
                        local_as.v6_pfx_n_covered_by_peers.remove(prefix)
                else:
                    local_as.peers_wo_cover_v6_pfx[peer_as.asn] += 1

        local_as.to_json(
            cli_args.uncompressed,
            get_output_filename(str(local_as.asn), True, cli_args.output),
        )

    print("")
    print_prefix_coverage(all_as_stats)
    print_t1_prefix_preference(all_as_stats)


def is_full_asn_table(asn: int) -> bool:
    asn_data = get_asn_report()
    full = asn_data[str(asn)]["asn_full"]
    assert isinstance(full, bool)
    return full


def is_full_v4_table(asn: int) -> bool:
    asn_data = get_asn_report()
    full = asn_data[str(asn)]["v4_full"]
    assert isinstance(full, bool)
    return full


def is_full_v6_table(asn: int) -> bool:
    asn_data = get_asn_report()
    full = asn_data[str(asn)]["v6_full"]
    assert isinstance(full, bool)
    return full


def parse_asn_file(filename: str) -> Optional[str]:
    """
    Load and parse a per-ASN AsnRoutes JSON file.
    As the data is loaded in, pre-calculate some stats used later.
    """

    print(f"{os.getpid()}: Loading {filename}...")
    if os.path.splitext(filename)[1] == ".gz":
        with gzip.open(filename, "rb") as f:
            asn_routes = AsnRoutes.from_dict(orjson.loads(f.read()))
    else:
        with open(filename) as f:
            asn_routes = AsnRoutes.from_dict(orjson.loads(f.read()))

    # Skip files which aren't for an ASNs of interest:
    if skip_asn(asn_routes.peer_as):
        print(f"{os.getpid()}: Skipping {asn_routes.peer_as}, not of interest")
        return None

    as_stats = AsStats(
        asn=asn_routes.peer_as,
        v4_percent=0.0,
        v6_percent=0.0,
        v4_pfx_tree=pytricia.PyTricia(IPV4_SIZE),
        v6_pfx_tree=pytricia.PyTricia(IPV6_SIZE),
        as_path_lengths={},
        avg_as_path_length=0,
        weighted_as_path_score=0,
        as_hops={},
        as_hops_freq={},
        avg_as_hops=0,
        weighted_as_hops_score=0,
        peers_w_cover_v4_pfx={},
        peers_wo_cover_v4_pfx={},
        v4_pfx_covered_by_peers=set(),
        v4_pfx_n_covered_by_peers=set(),
        v4_pfx_preferred_by_t1s=set(),
        v4_pfx_n_preferred_by_t1s=set(),
        peers_w_cover_v6_pfx={},
        peers_wo_cover_v6_pfx={},
        v6_pfx_covered_by_peers=set(),
        v6_pfx_n_covered_by_peers=set(),
        v6_pfx_preferred_by_t1s=set(),
        v6_pfx_n_preferred_by_t1s=set(),
        asns_reachable=set(),
        asns_reachable_via_peers=set(),
        asns_n_reachable_via_peers=set(),
        peers_w_reachable_asn={},
        peers_wo_reachable_asn={},
        on_net_asns=set(),
        asns_on_net_for_peers=set(),
        asns_n_on_net_for_peers=set(),
        peers_w_asn_on_net={},
        peers_wo_asn_on_net={},
    )

    """
    Pre-populate v4 and v6 data from the loaded routes
    """
    print(f"{os.getpid()}: Populating prefixes for {as_stats.asn}")
    for prefix in asn_routes.routes.keys():
        if BogonPrefixes.is_bogon(prefix):
            continue
        mask = int(prefix.split("/")[1])
        if ":" in prefix:
            """
            Some networks export prefixes to public collectors which aren't
            reachable outside that network
            """
            if mask > 48 or mask < 16:
                continue
            """
            Some networks export a default route
            """
            if prefix == "::/0":
                continue
            as_stats.v6_pfx_tree.insert(prefix, None)
            as_stats.v6_pfx_n_covered_by_peers.add(prefix)
            as_stats.v6_pfx_n_preferred_by_t1s.add(prefix)
        else:
            if mask > 24 or mask < 8:
                continue
            if prefix == "0.0.0.0/0":
                continue
            as_stats.v4_pfx_tree.insert(prefix, None)
            as_stats.v4_pfx_n_covered_by_peers.add(prefix)
            as_stats.v4_pfx_n_preferred_by_t1s.add(prefix)

    """
    Pre-populate ASN data from the loaded routes.

    Create a set of de-duped on-net ASNs.
    """
    print(f"{os.getpid()}: Populating ASNs for {as_stats.asn}")

    for as_paths in asn_routes.routes.values():
        for as_path in as_paths:

            for asn in as_path[:]:
                if BogonAsns.is_bogon(asn):
                    as_path.remove(asn)

            path_len = len(as_path)
            # It was a path of entirely bogon ASNs
            assert path_len, f"{os.getpid()}: null AS path after bogon removal"

            as_stats.asns_reachable.update(as_path)
            as_stats.asns_n_reachable_via_peers.update(as_path)

            """
            Record the AS path lengths as we go, later calculate avg.

            All paths start with the network's own ASN, which makes the AS paths
            1 hop longer than they are when referring to external connectivity.
            """
            if (path_len - 1) not in as_stats.as_path_lengths:
                as_stats.as_path_lengths[path_len - 1] = 1
            else:
                as_stats.as_path_lengths[path_len - 1] += 1

            """
            An ASN might be reachable via paths of varying lengths.
            Only count the shortest path, and remove count of existing longer
            path.
            Later calculate avg.
            """
            for idx, asn in enumerate(as_path):
                for hop_count in as_stats.as_hops.keys():
                    if int(asn) in as_stats.as_hops[hop_count]:
                        # Found the AS with a higher hop count
                        if hop_count > idx:
                            # Remove it and store at lower hop count
                            as_stats.as_hops[hop_count].remove(int(asn))
                            if idx not in as_stats.as_hops:
                                as_stats.as_hops[idx] = set()
                            as_stats.as_hops[idx].add(int(asn))
                            break
                        # Found AS with same of lower hop count
                        if hop_count <= idx:
                            # No need to store this hop count
                            break
                else:
                    # Didn't find the ASN yet, store hop count
                    if idx not in as_stats.as_hops:
                        as_stats.as_hops[idx] = set()
                    as_stats.as_hops[idx].add(int(asn))

            if path_len == 1:
                """
                A pfx originated by the local ASN.
                Don't include this in the set of reachable ASNs, self
                reachability is implicit:
                as_stats.on_net_asns.add(as_path[0])
                """
                as_stats.asns_n_on_net_for_peers.add(as_path[0])
            elif path_len > 1:
                """
                Ensure the first ASN is the local ASN which ensures the next
                ASN is the peer ASN
                """
                assert int(as_path[0]) == as_stats.asn
                as_stats.on_net_asns.add(as_path[1])
                as_stats.asns_n_on_net_for_peers.add(as_path[1])

    assert sum([x for x in as_stats.as_path_lengths.values()]) == sum(
        [len(as_path) for as_path in asn_routes.routes.values()]
    )

    assert sum([len(x) for x in as_stats.as_hops.values()]) == len(
        as_stats.asns_reachable
    )

    # Calculate the mode AS path length
    modes = [
        k
        for k in as_stats.as_path_lengths
        if as_stats.as_path_lengths[k]
        == max(as_stats.as_path_lengths.values())
    ]
    if len(modes) != 1:
        raise ValueError(
            f"Exactly one mode wasn't found, for AS path lengths of "
            f"AS{as_stats.asn}: {modes}"
        )
    as_stats.avg_as_path_length = modes[0]

    """
    Calculate a weighted AS path length score.
    Only includes AS path whose length is <= 10, above 10 is kinda garbage,
    any prefixes with a genuine AS path length > 10, make a tiny percentage.
    """
    max_hops = 11
    for path_length, frequency in as_stats.as_path_lengths.items():
        if path_length > 0 and path_length < max_hops:
            as_stats.weighted_as_path_score += (
                max_hops - path_length
            ) * frequency

    # Calculate the mode AS hop length
    for hop_count in as_stats.as_hops:
        as_stats.as_hops_freq[hop_count] = len(as_stats.as_hops[hop_count])

    modes = [
        k
        for k in as_stats.as_hops_freq
        if as_stats.as_hops_freq[k] == max(as_stats.as_hops_freq.values())
    ]
    if len(modes) != 1:
        raise ValueError(
            f"Exactly one mode wasn't found, for AS hop counts of "
            f"AS{as_stats.asn}: {modes}"
        )
    as_stats.avg_as_hops = modes[0]

    # Calculate a weighted AS hops score
    for as_hops, frequency in as_stats.as_hops_freq.items():
        if as_hops > 0 and as_hops < 11:
            as_stats.weighted_as_hops_score += (max_hops - as_hops) * frequency

    """
    Pre-populate AS path shortest via a tier 1, for each prefix.
    """
    print(f"{os.getpid()}: Populating tier 1 paths for {as_stats.asn}")

    for prefix, as_paths in asn_routes.routes.items():
        best_paths: list[list[int]] = []

        for as_path in as_paths:
            for asn in as_path[:]:
                if BogonAsns.is_bogon(asn):
                    as_path.remove(asn)

            path_len = len(as_path)
            # It was a path of entirely bogon ASNs
            assert (
                path_len
            ), f"{os.getpid()}: empty AS path after bogon removal"

            # First ASN is always the local ASN
            if path_len == 1:
                best_paths = [[]]
                continue

            # Remove the local ASN
            as_path.remove(as_stats.asn)

            # Is this a new shortest AS path?
            if not best_paths:
                best_paths.append(as_path)
            else:
                if path_len > len(best_paths[0]):
                    continue
                elif path_len == len(best_paths[0]):
                    if as_path not in best_paths:
                        best_paths.append(as_path)
                elif path_len < len(best_paths[0]):
                    best_paths = [as_path]

        # Are any of the first hops Tier 1 ASNs?
        for as_path in best_paths:
            # Locally originated prefix
            if len(as_path) == 0:
                if "." in prefix:
                    as_stats.v4_pfx_n_preferred_by_t1s.add(prefix)
                else:
                    as_stats.v6_pfx_n_preferred_by_t1s.add(prefix)
                break

            if is_tier1(as_path[0]):
                if "." in prefix:
                    as_stats.v4_pfx_preferred_by_t1s.add(prefix)
                    if prefix in as_stats.v4_pfx_n_preferred_by_t1s:
                        as_stats.v4_pfx_n_preferred_by_t1s.remove(prefix)
                else:
                    as_stats.v6_pfx_preferred_by_t1s.add(prefix)
                    if prefix in as_stats.v6_pfx_n_preferred_by_t1s:
                        as_stats.v6_pfx_n_preferred_by_t1s.remove(prefix)
                break
        else:
            if "." in prefix:
                as_stats.v4_pfx_n_preferred_by_t1s.add(prefix)
            else:
                as_stats.v6_pfx_n_preferred_by_t1s.add(prefix)

    print(
        f"{os.getpid()}: Parsed {len(as_stats.asns_reachable)} ASNs, "
        f"{len(as_stats.v4_pfx_tree)} v4 prefixes, "
        f"{len(as_stats.v6_pfx_tree)} v6 prefixes, "
        f"for {as_stats.asn}"
    )

    out_filename = get_output_filename(
        str(as_stats.asn), True, cli_args.output
    )
    as_stats.to_json(cli_args.uncompressed, out_filename)
    return out_filename


def parse_asn_files(asn_list: list[int]) -> list[str]:
    """
    Parse a list of AsnRoutes files.
    Spread this over multiple processes.
    """

    filenames: list[str] = get_input_filenames(
        asn_list, not cli_args.uncompressed
    )
    print(f"Loading {len(filenames)} input files")

    pool = multiprocessing.Pool(cli_args.p)
    results = pool.map(parse_asn_file, filenames)
    pool.close()
    gc.collect()

    # Remove skipped files
    as_stats_files = [f for f in results if f]

    print(f"Successfully parsed {len(as_stats_files)} files")
    print("")
    return as_stats_files


def print_as_cone_coverage(all_as_stats: list[AsStats]) -> None:
    """
    Print the stats about ASN reachability for each network
    """

    # Sort by AS number for results table
    all_as_stats = sorted(all_as_stats, key=lambda as_stats: as_stats.asn)
    as_numbers = [a.asn for a in all_as_stats]

    table_data: list[list[str]] = []

    for as_stats in all_as_stats:
        reachable_asn_count = len(as_stats.asns_reachable)
        global_asn_reachable_pct = (
            reachable_asn_count / len(GlobalStats.all_asns) * 100
        )
        asns_reachable_via_peers = len(as_stats.asns_reachable_via_peers)
        asns_reachable_via_peers_pct = (
            asns_reachable_via_peers / reachable_asn_count
        ) * 100
        asns_n_reachable_via_peers = len(as_stats.asns_n_reachable_via_peers)
        asns_n_reachable_via_peers_pct = (
            asns_n_reachable_via_peers / reachable_asn_count
        ) * 100
        row = [
            f"{as_stats.asn}",
            f"{asns[as_stats.asn].name.replace(',', ' ')}",
            f"{asns[as_stats.asn].tier_1}",
            f"{reachable_asn_count}",
            f"{global_asn_reachable_pct:.2f}",
            f"{asns_reachable_via_peers}",
            f"{asns_reachable_via_peers_pct:.2f}",
            f"{asns_n_reachable_via_peers}",
            f"{asns_n_reachable_via_peers_pct:.2f}",
        ]
        for as_n in as_numbers:
            if as_n == as_stats.asn:
                row.append("X")
                row.append("X")
            else:
                peer_coverage = as_stats.peers_w_reachable_asn[as_n]
                peer_coverage_pct = (peer_coverage / reachable_asn_count) * 100
                row.append(f"{peer_coverage}")
                row.append(f"{peer_coverage_pct:.2f}")
        table_data.append(row)

    table_headers = [
        "ASN",
        "Name",
        "T1",
        "AS Cone",
        "% of all ASNs",
        "ASNs Reachable Via Other Networks",
        "% ASNs Reachable Via Other Networks",
        "ASNs Not Reachable Via Other Networks",
        "% ASNs Not Reachable Via Other Networks",
    ]
    for as_stats in all_as_stats:
        table_headers.append(f"ASN Overlap {as_stats.asn}")
        table_headers.append(f"% ASN Overlap {as_stats.asn}")

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("AS cone coverage for each network:")
    print(table)

    write_csv(COVERAGE_AS_CONE, table_headers, table_data)
    print("")


def print_as_hops(all_as_stats: list[AsStats]) -> None:
    """
    Print the stats about hop count to other ASNs
    """

    # Sort by AS number for results table
    all_as_stats = sorted(all_as_stats, key=lambda as_stats: as_stats.asn)

    table_data: list[list[str]] = []

    all_as_hop_counts: set[int] = set()
    for as_stats in all_as_stats:
        all_as_hop_counts.update(list(as_stats.as_hops_freq.keys()))

    for as_stats in all_as_stats:
        row = [
            f"{as_stats.asn}",
            f"{asns[as_stats.asn].name.replace(',', ' ')}",
            f"{asns[as_stats.asn].tier_1}",
            f"{as_stats.avg_as_hops}",
            f"{as_stats.weighted_as_hops_score}",
        ]
        for hop_count in list(all_as_hop_counts):
            if hop_count in as_stats.as_hops_freq:
                row.append(f"{as_stats.as_hops_freq[hop_count]}")
                pct = (
                    as_stats.as_hops_freq[hop_count]
                    / len(as_stats.asns_reachable)
                    * 100
                )
                row.append(f"{pct:.2f}")
            else:
                row.append("X")
                row.append("X")

        table_data.append(row)

    table_headers = [
        "ASN",
        "Name",
        "T1",
        "Mode Hop Count",
        "Weighted Hop Count",
    ]

    for hop_count in all_as_hop_counts:
        table_headers.append(f"{hop_count}")
        table_headers.append(f"% {hop_count}")

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("AS hop count for each network:")
    print(table)

    write_csv(COVERAGE_AS_HOP_COUNT_ASNS, table_headers, table_data)
    print("")


def print_as_path_length(all_as_stats: list[AsStats]) -> None:
    """
    Print the stats about AS path length for each network per prefix
    """

    # Sort by AS number for results table
    all_as_stats = sorted(all_as_stats, key=lambda as_stats: as_stats.asn)

    table_data: list[list[str]] = []

    all_path_lengths: set[int] = set()
    for as_stats in all_as_stats:
        all_path_lengths.update(list(as_stats.as_path_lengths.keys()))

    for as_stats in all_as_stats:
        row = [
            f"{as_stats.asn}",
            f"{asns[as_stats.asn].name.replace(',', ' ')}",
            f"{asns[as_stats.asn].tier_1}",
            f"{as_stats.avg_as_path_length}",
            f"{as_stats.weighted_as_path_score}",
        ]
        for path_length in all_path_lengths:
            if path_length in as_stats.as_path_lengths:
                row.append(f"{as_stats.as_path_lengths[path_length]}")
            else:
                row.append("X")
        table_data.append(row)

    table_headers = [
        "ASN",
        "Name",
        "T1",
        "Mode Path Length",
        "Weighted Path Length",
    ]

    for path_length in all_path_lengths:
        table_headers.append(f"{path_length}")

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("AS path length for each network:")
    print(table)

    write_csv(COVERAGE_AS_HOP_COUNT_PREFIXES, table_headers, table_data)
    print("")


def print_continent_breakdown(all_as_stats: list[AsStats]) -> None:
    """
    Print the percent of directly connected ASNs which are allocated in
    each continent, to show any continental differences between networks.
    """

    continent_mappings = get_asn_to_continent_mappings(
        os.path.join(RAW_DATA, NRO_ALLOCATIONS)
    )
    continents: set[str] = set(list(continent_mappings.values()))

    table_data: list[list[str]] = []
    table_headers = ["ASN", "Name", "T1", "Directly Connected ASNs"]
    for continent in continents:
        table_headers.append(continent)
        table_headers.append(f"% {continent}")

    # Sort by AS number for results table
    all_as_stats = sorted(all_as_stats, key=lambda as_stats: as_stats.asn)

    for as_stats in all_as_stats:
        continent_count: dict[str, int] = {
            continent: 0 for continent in continents
        }

        for asn in as_stats.as_hops[1]:
            continent_count[continent_mappings[asn]] += 1

        row = [
            f"{as_stats.asn}",
            f"{asns[as_stats.asn].name.replace(',', ' ')}",
            f"{asns[as_stats.asn].tier_1}",
            f"{len(as_stats.as_hops[1])}",
        ]

        for continent in continents:
            row.append(f"{continent_count[continent]}")
            pct = (continent_count[continent] / len(as_stats.as_hops[1])) * 100
            row.append(f"{pct:.2f}")

        table_data.append(row)

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("Continents of directly connected ASNs:")
    print(table)

    write_csv(COVERAGE_CONTINENT_BREAKDOWN, table_headers, table_data)
    print("")


def print_peer_coverage(all_as_stats: list[AsStats]) -> None:
    """
    Print the percentage of all ASNs which are peered with each network
    """

    # Sort by AS number for results table
    all_as_stats = sorted(all_as_stats, key=lambda as_stats: as_stats.asn)

    table_data: list[list[str]] = []

    for idx, as_stats in enumerate(all_as_stats):
        on_net_asn_count = len(as_stats.on_net_asns)
        on_net_asn_pct = on_net_asn_count / len(GlobalStats.all_asns) * 100
        on_net_asns_covered_by_peers = len(as_stats.asns_on_net_for_peers)
        on_net_asns_covered_by_peers_pct = (
            on_net_asns_covered_by_peers / on_net_asn_count
        ) * 100
        asns_n_covered_by_peers = len(as_stats.asns_n_on_net_for_peers)
        asns_n_covered_by_peers_pct = (
            asns_n_covered_by_peers / on_net_asn_count
        ) * 100
        row = [
            f"{as_stats.asn}",
            f"{asns[as_stats.asn].name.replace(',', ' ')}",
            f"{asns[as_stats.asn].tier_1}",
            f"{on_net_asn_count}",
            f"{on_net_asn_pct:.2f}",
            f"{on_net_asns_covered_by_peers}",
            f"{on_net_asns_covered_by_peers_pct:.2f}",
            f"{asns_n_covered_by_peers}",
            f"{asns_n_covered_by_peers_pct:.2f}",
        ]
        for peer_coverage in as_stats.peers_w_asn_on_net.values():
            row.append(f"{peer_coverage}")
            row.append(f"{(peer_coverage / on_net_asn_count) * 100:.2f}")
        row.insert(idx + (idx * 1) + 9, "X")
        row.insert(idx + (idx * 1) + 10, "X")
        table_data.append(row)

    table_headers = [
        "ASN",
        "Name",
        "T1",
        "Peer ASNs",
        "% of all ASNs",
        "Non-Unique Peer ASNs",
        "% Non-Unique Peer ASNs",
        "Unique Peer ASNs",
        "% Unique Peer ASNs",
    ]
    for as_stats in all_as_stats:
        table_headers.append(f"Peering Overlap {as_stats.asn}")
        table_headers.append(f"% Peering Overlap {as_stats.asn}")

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("Peering coverage for each network:")
    print(table)

    write_csv(COVERAGE_PEERING, table_headers, table_data)
    print("")


def print_peerings(all_as_stats: list[AsStats]) -> None:
    """
    Print a matrix of peering between networks
    """

    keyed_as_stats = {as_stats.asn: as_stats for as_stats in all_as_stats}
    all_asns = sorted(
        [asn.asn for asn in asns.values() if asn.tier_1]
    ) + sorted([asn.asn for asn in asns.values() if not asn.tier_1])
    table_data: list[list[str]] = []

    for local_asn in all_asns:
        if local_asn not in keyed_as_stats:
            continue

        row = [
            str(local_asn),
            f"{asns[local_asn].name.replace(',', ' ')}",
            f"{asns[local_asn].tier_1}",
        ]
        total = 0
        for peer_asn in all_asns:
            if local_asn == peer_asn:
                row.append("X")
                continue

            peering = peer_asn in keyed_as_stats[local_asn].on_net_asns
            if peering:
                total += 1
            row.append(str(peering))

        row.insert(3, str(total))

        table_data.append(row)

    table_headers = ["ASN", "Name", "T1", "Count"]
    table_headers += [str(asn) for asn in all_asns]

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("T1 peering coverage for each network:")
    print(table)

    write_csv(COVERAGE_PEERINGS, table_headers, table_data)
    print("")


def print_ip_coverage(results: list[IpCoverage]) -> None:
    """
    Print the percentage of IP space which is on-net network for each network
    """

    table_headers = [
        "ASN",
        "Name",
        "T1",
        "% On-Net v4 Space",
        "% On-Net v6 Space",
    ]
    table_data: list[list[str]] = []

    for result in results:
        table_data.append(
            [
                f"{result.asn}",
                f"{asns[result.asn].name.replace(',', ' ')}",
                f"{asns[result.asn].tier_1}",
                f"{result.v4_percent:.2f}",
                f"{result.v6_percent:.2f}",
            ]
        )

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("IP address space coverage for each network:")
    print(table)

    write_csv(COVERAGE_IP, table_headers, table_data)
    print("")


def print_prefix_coverage(all_as_stats: list[AsStats]) -> None:
    """
    Print the percentage of IP prefixes which are on-net for each network
    """

    # Sort by AS number for results table
    all_as_stats = sorted(all_as_stats, key=lambda as_stats: as_stats.asn)
    as_numbers = [a.asn for a in all_as_stats]

    # IPv4 prefix coverage
    table_data: list[list[str]] = []

    for as_stats in all_as_stats:
        if not is_full_v4_table(as_stats.asn):
            continue
        pfx_count = len(as_stats.v4_pfx_tree)
        pfx_covered_by_peers = len(as_stats.v4_pfx_covered_by_peers)
        pfx_covered_by_peers_pct = (
            (pfx_covered_by_peers / pfx_count) * 100 if pfx_count else 100.0
        )
        pfx_n_covered_by_peers = len(as_stats.v4_pfx_n_covered_by_peers)
        pfx_n_covered_by_peers_pct = (
            (pfx_n_covered_by_peers / pfx_count) * 100 if pfx_count else 0.0
        )
        row = [
            f"{as_stats.asn}",
            f"{asns[as_stats.asn].name.replace(',', ' ')}",
            f"{asns[as_stats.asn].tier_1}",
            f"{pfx_count}",
            f"{pfx_covered_by_peers}",
            f"{pfx_covered_by_peers_pct:.2f}",
            f"{pfx_n_covered_by_peers}",
            f"{pfx_n_covered_by_peers_pct:.2f}",
        ]

        for as_n in as_numbers:
            if as_n == as_stats.asn:
                row.append("X")
                row.append("X")
                continue

            if not is_full_v4_table(as_n):
                continue

            peer_coverage = as_stats.peers_w_cover_v4_pfx[as_n]
            peer_coverage_pct = (
                (peer_coverage / pfx_count) * 100 if pfx_count else 100.0
            )
            row.append(f"{peer_coverage}")
            row.append(f"{peer_coverage_pct:.2f}")

        table_data.append(row)

    table_headers = [
        "ASN",
        "Name",
        "T1",
        "Reachable Pfxs",
        "Covered by Any Other Network",
        "% Covered by Any Other Network",
        "Not Covered by Any Other Network",
        "% Not Covered by Any Other Network",
    ]

    for as_stats in all_as_stats:
        if not is_full_v4_table(as_stats.asn):
            continue
        table_headers.append(f"Covered By {as_stats.asn}")
        table_headers.append(f"% Covered By {as_stats.asn}")

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("v4 prefix coverage for each network:")
    print(table)

    write_csv(COVERAGE_V4, table_headers, table_data)
    print("")

    # IPv6 prefix coverage
    table_data = []

    for as_stats in all_as_stats:
        if not is_full_v6_table(as_stats.asn):
            continue
        pfx_count = len(as_stats.v6_pfx_tree)
        pfx_covered_by_peers = len(as_stats.v6_pfx_covered_by_peers)
        pfx_covered_by_peers_pct = (
            pfx_covered_by_peers / pfx_count * 100 if pfx_count else 100.0
        )
        pfx_n_covered_by_peers = len(as_stats.v6_pfx_n_covered_by_peers)
        pfx_n_covered_by_peers_pct = (
            pfx_n_covered_by_peers / pfx_count * 100 if pfx_count else 0.0
        )
        row = [
            f"{as_stats.asn}",
            f"{asns[as_stats.asn].name.replace(',', ' ')}",
            f"{asns[as_stats.asn].tier_1}",
            f"{pfx_count}",
            f"{pfx_covered_by_peers}",
            f"{pfx_covered_by_peers_pct:.2f}",
            f"{pfx_n_covered_by_peers}",
            f"{pfx_n_covered_by_peers_pct:.2f}",
        ]

        for as_n in as_numbers:
            if as_n == as_stats.asn:
                row.append("X")
                row.append("X")
                continue

            if not is_full_v6_table(as_n):
                continue

            peer_coverage = as_stats.peers_w_cover_v6_pfx[as_n]
            peer_coverage_pct = (
                (peer_coverage / pfx_count) * 100 if pfx_count else 100.0
            )
            row.append(f"{peer_coverage}")
            row.append(f"{peer_coverage_pct:.2f}")

        table_data.append(row)

    table_headers = [
        "ASN",
        "Name",
        "T1",
        "Reachable Pfxs",
        "Covered by Any Other Network",
        "% Covered by Any Other Network",
        "Not Covered by Any Other Network",
        "% Not Covered by Any Other Network",
    ]

    for as_stats in all_as_stats:
        if not is_full_v6_table(as_stats.asn):
            continue
        table_headers.append(f"Covered By {as_stats.asn}")
        table_headers.append(f"% Covered By {as_stats.asn}")

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("v6 prefix coverage for each network:")
    print(table)

    write_csv(COVERAGE_V6, table_headers, table_data)
    print("")


def print_t1_prefix_preference(all_as_stats: list[AsStats]) -> None:
    """
    Print the percentage of IP prefixes which have a shorter AS path via T1
    """

    # Sort by AS number for results table
    all_as_stats = sorted(all_as_stats, key=lambda as_stats: as_stats.asn)

    table_headers = [
        "ASN",
        "Name",
        "T1",
        "Reachable Pfxs",
        "Shorter Paths via Any Tier 1",
        "% Shorter Paths via Any Tier 1",
        "Not Shorter Paths via Any Tier 1",
        "% Not Shorter Paths via Any Tier 1",
    ]

    # IPv4 prefixes
    table_data: list[list[str]] = []

    for as_stats in all_as_stats:
        if not is_full_v4_table(as_stats.asn):
            continue
        pfx_count = len(as_stats.v4_pfx_tree)
        pfx_preferred_by_t1s = len(as_stats.v4_pfx_preferred_by_t1s)
        pfx_preferred_by_t1s_pct = (
            (pfx_preferred_by_t1s / pfx_count) * 100 if pfx_count else 100.0
        )
        pfx_n_covered_by_t1s = len(as_stats.v4_pfx_n_preferred_by_t1s)
        pfx_n_covered_by_t1s_pct = (
            (pfx_n_covered_by_t1s / pfx_count) * 100 if pfx_count else 0.0
        )
        row = [
            f"{as_stats.asn}",
            f"{asns[as_stats.asn].name.replace(',', ' ')}",
            f"{asns[as_stats.asn].tier_1}",
            f"{pfx_count}",
            f"{pfx_preferred_by_t1s}",
            f"{pfx_preferred_by_t1s_pct:.2f}",
            f"{pfx_n_covered_by_t1s}",
            f"{pfx_n_covered_by_t1s_pct:.2f}",
        ]

        table_data.append(row)

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("v4 prefix paths shorter via a tier 1:")
    print(table)

    write_csv(COVERAGE_V4_SHORTER_T1, table_headers, table_data)
    print("")

    # IPv6 prefixes
    table_data = []

    for as_stats in all_as_stats:
        if not is_full_v6_table(as_stats.asn):
            continue
        pfx_count = len(as_stats.v6_pfx_tree)
        pfx_preferred_by_t1s = len(as_stats.v6_pfx_preferred_by_t1s)
        pfx_preferred_by_t1s_pct = (
            (pfx_preferred_by_t1s / pfx_count) * 100 if pfx_count else 100.0
        )
        pfx_n_covered_by_t1s = len(as_stats.v6_pfx_n_preferred_by_t1s)
        pfx_n_covered_by_t1s_pct = (
            (pfx_n_covered_by_t1s / pfx_count) * 100 if pfx_count else 0.0
        )
        row = [
            f"{as_stats.asn}",
            f"{asns[as_stats.asn].name.replace(',', ' ')}",
            f"{asns[as_stats.asn].tier_1}",
            f"{pfx_count}",
            f"{pfx_preferred_by_t1s}",
            f"{pfx_preferred_by_t1s_pct:.2f}",
            f"{pfx_n_covered_by_t1s}",
            f"{pfx_n_covered_by_t1s_pct:.2f}",
        ]

        table_data.append(row)

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("v6 prefix paths shorter via a tier 1:")
    print(table)

    write_csv(COVERAGE_V6_SHORTER_T1, table_headers, table_data)
    print("")


def parse_cli_args() -> None:
    parser = argparse.ArgumentParser(
        description="Script to calculate statistics per ASN using JSON "
        "serialised AsnRoutes as input",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-asns",
        help="Comma separated list of ASNs to generate stats for. "
        "By default, only the ASNs with a full table view from "
        f"{FULL_TABLE_REPORT} are included. This option takes precedence if used.",
        type=str,
    )
    parser.add_argument(
        "-input",
        help="Path to merged AsnRoutes JSON files to parse as input. "
        "Ignored if -skip is used.",
        type=str,
        metavar="path",
        default=MERGED_PATHS_PATH,
    )
    parser.add_argument(
        "-na",
        help="Don't produce ASN coverage stats",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-ni",
        help="Don't produce IP coverage stats",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-np",
        help="Don't produce prefix coverage stats",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-output",
        help="Path to output directory for AsStats files",
        type=str,
        metavar="path",
        default=COVERAGE_DATA_PATH,
    )
    parser.add_argument(
        "-p",
        help="No. of processes to start",
        type=int,
        default=multiprocessing.cpu_count() - 1,
    )
    parser.add_argument(
        "-report",
        help="Path to full table report",
        type=str,
        metavar="path",
        default=FULL_TABLE_REPORT,
    )
    parser.add_argument(
        "-skip",
        help="Skip parsing AsnRoutes files, load existing parsed AStats files "
        "from a previous run",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-uncompressed",
        help="Read and write uncompressed files",
        default=False,
        action="store_true",
        required=False,
    )

    global cli_args
    cli_args = parser.parse_args()

    if cli_args.asns:
        cli_args.asns = cli_args.asns.split(",")

    if not os.path.exists(cli_args.output):
        os.makedirs(os.path.dirname(cli_args.output), exist_ok=True)
        print(f"Created folder: {cli_args.output}")

    if not os.path.exists(cli_args.input):
        raise FileExistsError(f"Input path doesn't exist: {cli_args.input}")

    if not os.path.isdir(cli_args.input):
        raise ValueError(f"Input must be a directory: {cli_args.input}")


def write_csv(
    filename: str, headers: list[str], rows: list[list[str]]
) -> None:
    filename = os.path.join(cli_args.output, filename)

    with open(filename, "w") as f:
        csv_writer = csv.writer(f)
        csv_writer.writerow(headers)
        csv_writer.writerows(rows)
    print(f"Wrote to {filename}")


def main() -> None:
    parse_cli_args()

    if not cli_args.skip:
        BogonAsns.load_allocated_asns(os.path.join(RAW_DATA, NRO_ALLOCATIONS))
        if cli_args.asns:
            parse_asn_files([int(asn) for asn in cli_args.asns])
        else:
            parse_asn_files(get_asns_full_table_any())

    if not cli_args.na:
        if cli_args.asns:
            asn_list = [int(asn) for asn in cli_args.asns]
        else:
            asn_list = get_asns_full_table_asn()

        as_stats_files = get_output_filenames(
            asn_list, not cli_args.uncompressed, cli_args.output
        )
        calculate_asn_coverage(as_stats_files)
        gc.collect()

    if not cli_args.ni:
        if cli_args.asns:
            asn_list = [int(asn) for asn in cli_args.asns]
        else:
            asn_list = get_asns_full_table_ip()

        as_stats_files = get_output_filenames(
            asn_list, not cli_args.uncompressed, cli_args.output
        )
        calculate_ip_coverage(as_stats_files)
        gc.collect()

    if not cli_args.np:
        if cli_args.asns:
            asn_list = [int(asn) for asn in cli_args.asns]
        else:
            asn_list = get_asns_full_table_ip()

        as_stats_files = get_output_filenames(
            asn_list, not cli_args.uncompressed, cli_args.output
        )
        calculate_prefix_coverage(as_stats_files)
        gc.collect()

    GlobalStats.to_json()


if __name__ == "__main__":
    main()
