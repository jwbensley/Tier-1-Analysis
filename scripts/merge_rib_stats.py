#!/usr/bin/env python3

import argparse
import gc
import gzip
import multiprocessing
import os
import sys
import tempfile
from typing import Union

import orjson
from inc.asns import asns
from inc.globals import MERGED_PATHS_PATH, RIB_PATHS_PATH
from inc.stats import AsnRoutes

cli_args: argparse.Namespace


def merge_results() -> None:
    """
    Return all AsnRoutes merged into one per ASN.
    Spin up multiple processes to make it faster.

    Load pairs of AsnRoute objects, writing the merged results to disk.
    Don't keep parsing the same objects between processes and updating them.
    Python multiprocessing can't handle this, we end up blocking down to a
    single thread again. Hence, keep loading and writing to disk, and just
    passing filenames to processes. Filth!
    """

    for asn in cli_args.asns:
        json_files: list[Union[str, None]] = []
        for input_dir in cli_args.input_dirs:
            if not cli_args.uncompressed:
                filename = os.path.join(input_dir, f"{asn}-routes.json.gz")
            else:
                filename = os.path.join(input_dir, f"{asn}-routes.json")
            if not os.path.exists(filename):
                raise FileExistsError(f"Input file doesn't exist: {filename}")
            json_files.append(filename)

        if not json_files:
            print(f"No files to merge for AS{asn}")
            continue

        print(f"Merging {len(json_files)} files for AS{asn}")

        # Merge pairs of files. If we have an odd number to merge,
        # one file will be merged with nothing.
        if len(json_files) % 2 != 0:
            json_files.append(None)

        all_tmp_files: set[str] = set()
        process_args: list[tuple[str | None, str | None]] = list(
            zip(json_files[::2], json_files[1::2], strict=True)
        )

        merging = True
        while merging:
            print(f"Merging {len(process_args)*2} files")
            pool = multiprocessing.Pool(cli_args.p)
            json_files = pool.map(merge_json_files, process_args)
            pool.close()
            gc.collect()

            for f in json_files:
                if f:
                    all_tmp_files.add(f)
            print(f"{len(json_files)} files left to merge")

            if len(json_files) > 1:
                # Ensure we have an even number of AsnRoutes to merge
                if len(json_files) % 2 != 0:
                    json_files.append(None)
                process_args = list(
                    zip(json_files[::2], json_files[1::2], strict=True)
                )
            else:
                merging = False

        if (json_file := json_files[0]) is not None:
            if not cli_args.uncompressed:
                with gzip.open(json_file, "rb") as f:
                    asn_routes = AsnRoutes.from_dict(orjson.loads(f.read()))
            else:
                with open(json_file) as f:
                    asn_routes = AsnRoutes.from_dict(orjson.loads(f.read()))
        else:
            raise ValueError("Missing filename to load")

        print(f"Finished merging AS{asn}")
        print(
            f"AS{asn}. Total: {asn_routes.v4_count + asn_routes.v6_count}, "
            f"v4: {asn_routes.v4_count}, v6: {asn_routes.v6_count}"
        )
        if cli_args.uncompressed:
            output_file = os.path.join(cli_args.output, f"{asn}-routes.json")
        else:
            output_file = os.path.join(
                cli_args.output, f"{asn}-routes.json.gz"
            )
        asn_routes.to_json(cli_args.uncompressed, output_file)

        for filename in all_tmp_files:
            os.unlink(filename)
        # print(f"Deleted {filename}")

        print("")

    print("All data merged")
    print("")


def merge_json_files(json_files: tuple[str | None, str | None]) -> str:
    """
    Load two AsnRoute route objs from JSON and return the first one
    with the routes from the second merged into the first one.
    This updated first obj is written back to disk to a tmp file.
    """
    f1, f2 = json_files

    assert f1
    print(f"{os.getpid()}: Loading 1st JSON file {f1}")
    if os.path.splitext(f1)[1] == ".gz":
        with gzip.open(f1, "rb") as f:
            try:
                f1_data = orjson.loads(f.read())
            except orjson.JSONDecodeError as e:
                print(f"Error loading 1st JSON file {f1}")
                raise e
    else:
        with open(f1) as f:
            try:
                f1_data = orjson.loads(f.read())
            except orjson.JSONDecodeError as e:
                print(f"Error loading 1st JSON file {f1}")
                raise e

    asn_routes_1 = AsnRoutes.from_dict(f1_data)
    print(
        f"{os.getpid()}: Parsed {len(asn_routes_1.routes)} "
        "routes from 1st JSON file"
    )

    if f2:
        print(f"{os.getpid()}: Loading 2nd JSON file {f2}")
        if os.path.splitext(f2)[1] == ".gz":
            with gzip.open(f2, "rb") as f:
                try:
                    f2_data = orjson.loads(f.read())
                except orjson.JSONDecodeError as e:
                    print(f"Error loading 2nd JSON file {f2}")
                    raise e
        else:
            with open(f2) as f:
                try:
                    f2_data = orjson.loads(f.read())
                except orjson.JSONDecodeError as e:
                    print(f"Error loading 2nd JSON file {f2}")
                    raise e
        asn_routes_2 = AsnRoutes.from_dict(f2_data)
    else:
        asn_routes_2 = AsnRoutes(peer_as=asn_routes_1.peer_as, routes={})
    print(
        f"{os.getpid()}: Parsed {len(asn_routes_2.routes)} "
        "routes from 2nd JSON file"
    )

    print(
        f"{os.getpid()}: Merging {len(asn_routes_1.routes)} with "
        f"{len(asn_routes_2.routes)} routes"
    )
    asn_routes_1.merge_asn_routes(asn_routes_2)
    print(f"{os.getpid()} Merged into {len(asn_routes_1.routes)} routes")

    _, filename = tempfile.mkstemp()
    if not cli_args.uncompressed:
        filename = filename + ".gz"
    asn_routes_1.to_json(cli_args.uncompressed, filename)
    return filename


def parse_cli_args() -> None:
    parser = argparse.ArgumentParser(
        description="Script to merge router from multiple JSON files, "
        "containing BGP routers from MRT files and CLI output, "
        "into a single JSON file per ASN",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-asns",
        help="Comma separated list of ASNs to look for in AS-paths",
        type=str,
        default=",".join([str(asn) for asn in sorted(asns.keys())]),
    )
    parser.add_argument(
        "-output",
        help="Path to output directory for merged routes",
        type=str,
        metavar="path",
        default=MERGED_PATHS_PATH,
    )
    parser.add_argument(
        "-p",
        help="No. of processes to start",
        type=int,
        default=multiprocessing.cpu_count() - 1,
    )
    parser.add_argument(
        "-uncompressed",
        help="Write uncompressed output files",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "input_dirs",
        help="Base path for data to be merged. "
        "This is folder, with a sub-folder per data source, "
        "each containing JSON files per ASN. "
        "This must be a file glob E.g. " + os.path.join(RIB_PATHS_PATH, "*"),
        type=str,
        nargs="*",
    )

    global cli_args
    cli_args = parser.parse_args()
    cli_args.asns = cli_args.asns.split(",")

    if not cli_args.input_dirs:
        print(
            "You must specify a glob of folders to search for JSON files "
            "to merge!"
        )
        print(f"{__file__} -h")
        sys.exit(1)


def main() -> None:
    parse_cli_args()

    print(
        f"Searching for routes to merge in {len(cli_args.input_dirs)} "
        f"sources from {len(cli_args.asns)} ASNs"
    )
    merge_results()
    print("Done.")


if __name__ == "__main__":
    main()
