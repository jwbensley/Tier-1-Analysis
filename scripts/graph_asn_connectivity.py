#!/usr/bin/env python3

from __future__ import annotations

import argparse
import gzip
import os

import matplotlib.pyplot as plt
import networkx as nx
import orjson
from inc.asns import asns
from inc.bogon_asns import BogonAsns
from inc.download import get_url_to_file
from inc.globals import (
    ASN_GRAPHS_PATH,
    MERGED_PATHS_PATH,
    NRO_ALLOCATIONS,
    RAW_DATA,
)

cli_args: argparse.Namespace


def download_nro_delegated_stats() -> str:
    """
    Download the list of ASNs assigned by the 5 RIRs
    """
    return get_url_to_file(
        filename=os.path.join(RAW_DATA, NRO_ALLOCATIONS),
        url="https://ftp.ripe.net/pub/stats/ripencc/nro-stats/latest/nro-delegated-stats",
    )


def get_filename(asn: str, compressed: bool, directory: str) -> str:
    """
    Return the filename for a AsnRoutes object serialised to JSON
    """
    filename = os.path.join(directory, f"{asn}-routes.json")
    if compressed:
        return filename + ".gz"
    if not os.path.exists(filename):
        raise FileExistsError(f"File doesn't exist: {filename}")
    return filename


def get_filenames(
    asn_list: list[str], compressed: bool, directory: str
) -> list[str]:
    """
    Return the list of AsnRoutes filenames based on the chosen ASNs
    """
    return [get_filename(asn, compressed, directory) for asn in asn_list]


def load_asn_data() -> dict[int, set[int]]:
    """
    For each ASN, built the list of ASN they are directly connected with
    """

    asns: dict[int, set[int]] = {}
    filenames = get_filenames(
        cli_args.asns, not cli_args.uncompressed, cli_args.input
    )

    BogonAsns.load_allocated_asns(os.path.join(RAW_DATA, NRO_ALLOCATIONS))

    for filename in filenames:
        print(f"Loading {filename}")

        data: dict
        if cli_args.uncompressed:
            with open(filename) as f:
                data = orjson.loads(f.read())
        else:
            with gzip.open(filename, "rt") as f:
                data = orjson.loads(f.read())

        print("Parsing data")
        as_paths: list[list[str]]
        for as_paths in data["routes"].values():
            for as_path in as_paths:

                if len(as_path) == 1:
                    local_asn = int(as_path[0])

                    # Don't include BOGON ASNs
                    if BogonAsns.is_bogon(local_asn):
                        continue

                    # Prefix originated by peer
                    if local_asn not in asns:
                        asns[local_asn] = set()
                    continue

                for i in range(len(as_path) - 1):
                    local_asn = int(as_path[i])
                    peer_asn = int(as_path[i + 1])

                    if BogonAsns.is_bogon(local_asn):
                        continue

                    if local_asn not in asns:
                        asns[local_asn] = set()

                    if BogonAsns.is_bogon(peer_asn):
                        continue

                    if peer_asn not in asns:
                        asns[peer_asn] = set()

                    if local_asn != peer_asn:
                        asns[local_asn].add(peer_asn)

    print(f"Loaded {len(asns)} ASNs")
    return asns


def build_graph() -> None:
    asns = load_asn_data()

    print("Building graph...")
    g: nx.Graph = nx.Graph()
    for asn, peers in asns.items():
        # Skip stub ASNs with no peers
        if len(peers) == 0:
            continue

        g.add_node(asn)
        for peer in peers:
            # Skip peers which are stub ASNs
            if len(asns[peer]) == 0:
                continue

            # Only add edges which are missing
            if not g.has_edge(asn, peer) and not g.has_edge(peer, asn):
                g.add_edge(asn, peer)

    print(f"Graph has {len(g.nodes)} nodes and {len(g.edges)} edges")

    print(f"Generating layout using: {cli_args.layout}...")

    if cli_args.layout == "kamada":
        pos = nx.kamada_kawai_layout(g)
    elif cli_args.layout == "arf":
        pos = nx.arf_layout(g)
    elif cli_args.layout == "spring":
        k = 1
        i = 30
        pos = nx.spring_layout(g, k=k, iterations=i, seed=63)
        # k controls the distance between the nodes and varies between 0 and 1
        # iterations is the number of times simulated annealing is run
        # default k=0.1 and iterations=50
        # Seed for layout reproducibility
    else:
        raise ValueError(f"Unknown layout: {cli_args.layout}")

    width = cli_args.dpi
    height = cli_args.dpi
    dpi = cli_args.dpi
    _ = plt.figure(1, figsize=(width, height), dpi=dpi)

    node_size: list[int] | int
    if cli_args.nodesizes:
        node_size = [len(asns[node]) for node in g.nodes]
    else:
        node_size = 1

    options = {
        "node_size": node_size,
        "node_color": "blue",
        "font_color": "red",
    }
    nx.draw_networkx(g, pos, **options)

    print("Rendering graph...")
    plt.axis("off")  # turn off axis
    plt.tight_layout()  # Reduce padding/margins
    plt.margins(0.0)  # Remove margins

    filename = f"graph_{len(asns)}_{width}_{height}_{dpi}_{cli_args.layout}"
    if cli_args.nodesizes:
        filename += "_nodesizes"
    filename += ".png"
    filename = os.path.join(ASN_GRAPHS_PATH, filename)

    plt.savefig(filename, format="png", bbox_inches='tight')
    print(f"Wrote to {filename}")


def parse_cli_args() -> None:
    parser = argparse.ArgumentParser(
        description="Script to generate a graph diagram of ASN connectivity",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-asns",
        help="Comma separated list of ASNs to load AsStats files for",
        type=str,
        default=",".join([str(asn) for asn in sorted(asns.keys())]),
    )
    parser.add_argument(
        "-dpi", help="Rendered graphic dots per inch", type=int, default=60
    )
    parser.add_argument(
        "-input",
        help="Path to AsnRoutes JSON files to parse as input",
        type=str,
        metavar="path",
        default=MERGED_PATHS_PATH,
    )
    parser.add_argument(
        "-layout",
        help="Networkx layout algo",
        choices=["arf", "kamada", "spring"],
        default="kamada",
    )
    parser.add_argument(
        "-nodesizes",
        help="Set the node size to be based on the number of peers",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-output",
        help="Path to output directory for rendered diagrams",
        type=str,
        metavar="path",
        default=ASN_GRAPHS_PATH,
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


def main() -> None:
    parse_cli_args()
    build_graph()


if __name__ == "__main__":
    main()
