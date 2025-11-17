#!/usr/bin/env python3

import argparse
import gc
import gzip
import multiprocessing
import os

import orjson
from inc.asns import asns
from inc.download import get_json_to_file
from inc.globals import (
    COVERAGE_DATA_PATH,
    FULL_TABLE_REPORT,
    MERGED_PATHS_PATH,
    RIS_THRESHOLDS,
)
from tabulate import tabulate

cli_args: argparse.Namespace


def download_ris_full_table_threshold() -> str:
    """
    Download the threshold defined by RIPE RIS used to decide if an ASN
    is carrying the full DFZ.
    """
    return get_json_to_file(
        filename=os.path.join(COVERAGE_DATA_PATH, RIS_THRESHOLDS),
        url="https://stat.ripe.net/data/ris-full-table-threshold/data.json",
    )


def get_ris_data() -> dict:
    ris_filename = download_ris_full_table_threshold()
    with open(ris_filename) as f:
        ris_data = orjson.loads(f.read())
    assert isinstance(ris_data, dict)
    return ris_data


def parse_asn_data(args: tuple[str, int, int, int]) -> dict[str, int | bool]:
    """
    Load and parse the stats for a single ASN
    """
    asn, asn_threshold, v4_threshold, v6_threshold = args

    filename = os.path.join(cli_args.input, f"{asn}-routes.json.gz")
    print(f"{os.getpid()}: Loading {filename}")
    if os.path.splitext(filename)[1] == ".gz":
        with gzip.open(filename, "rb") as f:
            asn_data = orjson.loads(f.read())
    else:
        with open(filename) as f:
            asn_data = orjson.loads(f.read())

    seen_asns: set[int] = set()
    as_paths: list[list[int]]
    for as_paths in asn_data["routes"].values():
        for as_path in as_paths:
            seen_asns.update(as_path)

    result = {
        "asn": int(asn),
        "v4_count": asn_data["v4_count"],
        "v4_full": asn_data["v4_count"] >= v4_threshold,
        "v6_count": asn_data["v6_count"],
        "v6_full": asn_data["v6_count"] >= v6_threshold,
        "asn_count": len(seen_asns),
        "asn_full": len(seen_asns) >= asn_threshold,
    }
    return result


def load_and_print_count(
    asn_threshold: int, v4_threshold: int, v6_threshold: int
) -> None:

    print(f"Looking for reconstructed tables in {cli_args.input}")
    print(
        f"Using thresholds: {asn_threshold} ASNs, {v4_threshold} v4, "
        f"{v6_threshold} v6"
    )

    table_data: list[list[str]] = []
    pool = multiprocessing.Pool(cli_args.p)
    process_args = [
        (asn, asn_threshold, v4_threshold, v6_threshold)
        for asn in cli_args.asns
    ]
    results: list[dict[str, int | bool]] = pool.map(
        parse_asn_data, process_args
    )
    pool.close()
    gc.collect()

    for result in sorted(results, key=lambda x: x["asn"]):
        table_data.append([str(v) for v in result.values()])

    table_headers = [
        "ASN",
        "V4 Pfxs",
        "V4 Full Table",
        "V6 Pfxs",
        "V6 Full Table",
        "ASNs",
        "ASNs Full Table",
    ]

    table = tabulate(table_data, headers=table_headers, tablefmt="grid")

    print("")
    print("Prefix count per ASN:")
    print(table)
    print("")
    write_json(
        {str(result["asn"]): result for result in results}, cli_args.output
    )


def parse_cli_args() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Script to check if the number of routes and ASNs in each "
            "reconstructed table meets the threshold to be considered a "
            "full table view. Minimum v4 and v6 limits are pulled from RIPE."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-asns",
        help="Comma separated list of ASNs, who's reconstructed tables will be "
        "checked",
        type=str,
        default=",".join([str(asn) for asn in sorted(asns.keys())]),
    )
    parser.add_argument(
        "-input",
        help="Path to input directory with JSON serialised AsnRoutes files",
        type=str,
        metavar="path",
        default=MERGED_PATHS_PATH,
    )
    parser.add_argument(
        "-output",
        help="Path to output file for storing results",
        type=str,
        metavar="path",
        default=FULL_TABLE_REPORT,
    )
    parser.add_argument(
        "-p",
        help="No. of processes to start",
        type=int,
        default=multiprocessing.cpu_count() - 1,
    )
    parser.add_argument(
        "-t4",
        help="Override the RIPE threshold for minimum v4 prefixes to consider "
        "the reconstructed table as holding the full v4 table",
        type=int,
    )
    parser.add_argument(
        "-t6",
        help="Override the RIPE threshold for minimum v6 prefixes to consider "
        "the reconstructed table as holding the full v4 table",
        type=int,
    )
    parser.add_argument(
        "-ta",
        help="Threshold for minimum ASNs to consider the reconstructed table "
        "as holding the full v4 table",
        type=int,
        default=75000,
    )

    global cli_args
    cli_args = parser.parse_args()
    cli_args.asns = cli_args.asns.split(",")


def write_json(data: dict, filename: str) -> None:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
    print(f"Wrote to {filename}")


def main() -> None:
    parse_cli_args()

    if cli_args.t4 and cli_args.t6:
        load_and_print_count(cli_args.ta, cli_args.t4, cli_args.t6)
    else:
        ris_data = get_ris_data()

        if not cli_args.t4:
            v4_threshold = int(ris_data["data"]["v4"])
        else:
            v4_threshold = cli_args.t4

        if not cli_args.t6:
            v6_threshold = int(ris_data["data"]["v6"])
        else:
            v6_threshold = cli_args.t6

        load_and_print_count(cli_args.ta, v4_threshold, v6_threshold)


if __name__ == "__main__":
    main()
