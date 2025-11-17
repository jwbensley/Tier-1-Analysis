#!/usr/bin/env python3

import argparse
import gc
import gzip
import ipaddress
import multiprocessing
import os
import random
import re
import sys
import traceback

import mrtparse  # type: ignore
from inc.asns import asns
from inc.globals import BGP_RIBS_PATH, RIB_PATHS_PATH
from inc.stats import AsnRoutes

cli_args: argparse.Namespace


def parse_cli_args() -> None:
    parser = argparse.ArgumentParser(
        description="Script to parse the BGP table dumps from collector into "
        "per-dump per-ASN JSON files. The type of dump is inferred from the "
        "filename e.g., files with *ios* in the name are assumed "
        "to be in Cisco IOS format. "
        f"Supported formats: {', '.join(file_formats.keys())}.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-asns",
        help="Comma separated list of ASNs to look for in AS-paths",
        type=str,
        default=",".join([str(asn) for asn in sorted(asns.keys())]),
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
        "-output",
        help="Path to output directory for extracted routes",
        type=str,
        metavar="path",
        default=RIB_PATHS_PATH,
    )
    parser.add_argument(
        "ribs",
        help="Glob of RIB files to parse. "
        "E.g. " + os.path.join(BGP_RIBS_PATH, "*.txt.gz"),
        type=str,
        nargs="*",
    )

    global cli_args
    cli_args = parser.parse_args()
    cli_args.asns = cli_args.asns.split(",")

    if not cli_args.ribs:
        print("You must specify a glob of RIB files to parse!")
        print(f"{__file__} -h")
        sys.exit(1)


def parse_file(filename: str) -> None:
    """
    For each input RIB file;
        decompress if GZIPed,
        create output path per input file
        pass to parser
    """

    print(f"{os.getpid()}: Parsing file {filename}", flush=True)

    if re.match("^rrc.*gz$", os.path.basename(filename).lower()) or re.match(
        "^route-views.*bz2", os.path.basename(filename).lower()
    ):
        print(f"{os.getpid()}: Assuming file is MRT format: {filename}")
        routes = parse_rib_data_mrt(filename)
    else:
        try:
            if os.path.splitext(filename)[1] == ".gz":
                with gzip.open(filename, "rt") as f:
                    raw_rib_data = f.read()
            else:
                with open(filename) as f:
                    raw_rib_data = f.read()
        except EOFError:
            # Sometimes the compressed file is corrupt and we reach EOF early
            print(
                f"{os.getpid()}: Skipping file because unexpected EOF reached: "
                f"{filename}\n"
                f"{traceback.format_exc()}"
            )
            return

        for os_type, parser in file_formats.items():
            if re.match(f".*{os_type.lower()}.*", filename.lower()):
                print(
                    f"{os.getpid()}: Assuming file is {os_type} format: {filename}"
                )
                routes = parser(raw_rib_data)
                break
        else:
            print(
                f"{os.getpid()}: Couldn't determine CLI format, defaulting to IOS: "
                f"{filename}"
            )
            routes = file_formats["ios"](raw_rib_data)

    output_dir = os.path.join(
        cli_args.output, os.path.splitext(os.path.basename(filename))[0]
    )
    for asn, asn_routes in routes.items():
        print(
            f"{os.getpid()}: AS{asn}. Total: "
            f"{asn_routes.v4_count + asn_routes.v6_count}, "
            f"v4: {asn_routes.v4_count}, v6: {asn_routes.v6_count}"
        )

        asn_filename = os.path.join(output_dir, f"{asn}-routes.json")
        if not cli_args.uncompressed:
            asn_filename = asn_filename + ".gz"
        asn_routes.to_json(cli_args.uncompressed, asn_filename)

    print(f"{os.getpid()}: Parsed file {filename}", flush=True)

    """
    Force garbage collection otherwise it doesn't run until all processes in
    the pool have joined()
    """
    routes = {}
    del routes
    gc.collect()


def parse_files() -> None:
    """
    Spin up multiple python processes.
    Each one searches for all paths via one of the passed ASNs,
    in a single RIB file, from the list of passed RIB files,
    one process per RIB file.
    """

    print(
        f"Searching for routes in {len(cli_args.ribs)} RIB files from "
        f"{len(cli_args.asns)} ASNs"
    )

    for filename in cli_args.ribs:
        if not os.path.isfile(filename):
            raise FileNotFoundError(filename)

    """
    Randomize the list of input files, to prevent long tail parsing of
    larger files. This also reduces memory usage because larger files aren't
    parsed in parallel, they are mixed with smaller files.
    """
    _ = cli_args.ribs[:]
    filenames: list[str] = []
    while len(_):
        i = random.randint(0, len(_) - 1)
        filenames.append(_.pop(i))

    pool = multiprocessing.Pool(cli_args.p)
    pool.map(parse_file, filenames)
    pool.close()

    print("All RIB files parsed.")
    print("")


def parse_rib_data_bird(raw_rib_data: str) -> dict[int, AsnRoutes]:
    """
    Parse each line of the RIB output and store the prefix against each ASN
    in the path.
    """

    routes: dict[int, AsnRoutes] = {
        int(asn): AsnRoutes(peer_as=int(asn), routes={})
        for asn in cli_args.asns
    }

    """
    Each file starts with a varying number of lines of text, which explains
    the "show" command output.

    The data starts on the line after "Table ...:"
    """
    skipping = True

    parsed_lines = 0
    current_prefix = ""
    new_prefix = ""

    for line in raw_rib_data.splitlines():

        # Skip blank lines
        if line.strip() == "":
            continue

        if skipping:
            # We found the first prefix
            try:
                ipaddress.ip_network(line.split()[0])
                skipping = False
            except ValueError:
                continue

        """
        If the line starts with a non-whitespace char, it's a new prefix.
        If it starts with whitespace, it's an attribute of the current prefix:

        1.0.0.0/24           unicast [xxxxx_v4 2025-08-25 from 169.254.169.254] * (100/?) [AS13335i]
        	via xx.xx.xxx.x on enp1s0
        	hostentry: via 169.254.169.254 table master4
        	preference: 100
        	from: 169.254.169.254
        	source: BGP
        	bgp_origin: IGP
        	bgp_path: 64515 20473 13335
        	bgp_next_hop: 169.254.169.254
        	bgp_local_pref: 100
        	bgp_aggregator: 10.34.8.168 AS13335
        	bgp_community: (20473,200) (20473,13335) (64515,44)
        	bgp_large_community: (20473, 200, 13335)
        	Internal route handling values: 0L 16G 0S id 19
        """

        if re.match(r"^\s", line):
            values = line.lstrip().split()
            if values[0] == "bgp_path:":
                as_path = values[1:]
            elif values[0] == "BGP.as_path:":
                as_path = (
                    line.replace("{", "")
                    .replace("}", "")
                    .split(":")[1]
                    .split()
                )

        else:
            new_prefix = line.split()[0]

            try:
                ipaddress.ip_network(new_prefix)
            except ValueError as e:
                print(f"{os.getpid()}: Unable to parse prefix: {line}")
                raise e

            # Setup for first routing entry
            if current_prefix == "":
                current_prefix = new_prefix

        """
        Found the next routing entry, which means all attributes of the
        previous entry have been parsed.
        """
        if new_prefix != current_prefix:

            """
            Skip default routes
            """
            if current_prefix == "0.0.0.0/0" or current_prefix == "::/0":
                print(
                    f"{os.getpid()}: Skipping default route: {current_prefix}"
                )
                current_prefix = new_prefix
                continue

            """
            De-dupe the AS path (remove prepends).

            Also, split atomic aggregates into individual ASNs (assume they are
            reachable):
            6939 1299 2711 14615 {36040,398053} -> 6939 1299 2711 14615 36040 398053
            This means the AS-path is not 100% accurate but atomic aggregates are
            pretty rare these days and decreasing further because AS-sets are being
            deprecated. It should make no noticeable difference to the overall stats
            produced. It idea here is just to record all ASNs reachable, even if
            the path length is mangled.
            """
            deduped_path: list[int] = []
            try:
                for entry in as_path:
                    # Bird CLI output truncates long AS paths!
                    if entry.endswith("..."):
                        continue
                    if "{" in entry or "}" in entry:
                        for sub_entry in entry.split(","):
                            asn = int(sub_entry.lstrip("{").rstrip("}"))
                            if asn not in deduped_path:
                                deduped_path.append(asn)
                    else:
                        if int(entry) not in deduped_path:
                            deduped_path.append(int(entry))
            except Exception as e:
                print(
                    f"{os.getpid()}:parse_rib_data_bird: "
                    f"Couldn't parse AS path: {as_path}"
                )
                raise e

            for asn in cli_args.asns:
                if int(asn) in deduped_path:
                    routes[int(asn)].add_prefix(
                        current_prefix,
                        deduped_path[deduped_path.index(int(asn)) :],
                    )

            current_prefix = new_prefix

        parsed_lines += 1

    print(f"{os.getpid()}: Parsed {parsed_lines} lines")
    return routes


def parse_rib_data_eos(raw_rib_data: str) -> dict[int, AsnRoutes]:
    """
    Parse each line of the RIB output and store the prefix against each ASN
    in the path.
    """

    routes: dict[int, AsnRoutes] = {
        int(asn): AsnRoutes(peer_as=int(asn), routes={})
        for asn in cli_args.asns
    }

    """
    Each file starts with a varying number of lines of text, which explains
    the "show" command output. Some collectors support RPKI and others don't
    for example, which causes the output length to vary.

    The data starts on the line after the line with the following column
    headings: Network, Next Hop, Metric..."
    """
    skipping = True

    parsed_lines = 0

    for line in raw_rib_data.splitlines():

        # Skip blank lines
        if line.strip() == "":
            continue

        # Skip the heading info
        if skipping:
            if re.match(r"\s+Network\s+Next Hop\s+Metric.*", line):
                skipping = False
                continue
            else:
                continue

        # The last character on each line is the Unknown/EGP/IGP origin flag:
        line = line.rstrip("?").rstrip("e").rstrip("i")

        """
        Rather than having a varying number of characters (flags) before the
        prefix column, EOS has a fixed number of 10 chars/columns.

                          Network                Next Hop              Metric  AIGP       LocPref Weight  Path
         * >    U 1.0.4.0/24             xxx.xxx.xx.xx         -       -          -       -       1299 7545 38803 i
        """
        line = line[10:]

        values = line.split()
        prefix = values[0]
        as_path = values[6:]

        try:
            ipaddress.ip_network(prefix)
        except ValueError as e:
            print(f"{os.getpid()}: Unable to parse prefix: {line}")
            raise e

        """
        Skip default routes
        """
        if prefix == "0.0.0.0/0" or prefix == "::/0":
            print(f"{os.getpid()}: Skipping default route: {line}")
            continue

        """
        De-dupe the AS path (remove prepends).

        Also, split atomic aggregates into individual ASNs (assume they are
        reachable):
        6939 1299 2711 14615 {36040,398053} -> 6939 1299 2711 14615 36040 398053
        This means the AS-path is not 100% accurate but atomic aggregates are
        pretty rare these days and decreasing further because AS-sets are being
        deprecated. It should make no noticeable difference to the overall stats
        produced. It idea here is just to record all ASNs reachable, even if
        the path length is mangled.
        """
        deduped_path: list[int] = []
        try:
            for entry in as_path:
                if "{" in entry or "}" in entry:
                    for sub_entry in entry.split(","):
                        asn = int(sub_entry.lstrip("{").rstrip("}"))
                        if asn not in deduped_path:
                            deduped_path.append(asn)
                else:
                    if int(entry) not in deduped_path:
                        deduped_path.append(int(entry))
        except Exception as e:
            print(
                f"{os.getpid()}:parse_rib_data_eos: "
                f"Couldn't parse AS path: {as_path}"
            )
            raise e

        for asn in cli_args.asns:
            if int(asn) in deduped_path:
                routes[int(asn)].add_prefix(
                    prefix, deduped_path[deduped_path.index(int(asn)) :]
                )

        parsed_lines += 1

    print(f"{os.getpid()}: Parsed {parsed_lines} lines")
    return routes


def parse_rib_data_ios(raw_rib_data: str) -> dict[int, AsnRoutes]:
    """
    Parse each line of the RIB output and store the prefix against each ASN
    in the path.
    """

    routes: dict[int, AsnRoutes] = {
        int(asn): AsnRoutes(peer_as=int(asn), routes={})
        for asn in cli_args.asns
    }

    """
    Each file starts with a varying number of lines of text, which explains
    the "show" command output. Some collectors support RPKI and others don't
    for example, which causes the output length to vary.

    The data starts on the line after the line with the following column
    headings: Network, Next Hop, Metric..."
    """
    skipping = True

    """
    A prefix may have multiple paths, but the prefix is only listed once.
    """
    current_prefix = ""

    parsed_lines = 0

    """
    Reconstruct output split over multiple lines
    """
    split_lines: list[str] = []
    append_next = False

    for line in raw_rib_data.splitlines():

        # Skip blank lines
        if line.strip() == "":
            continue

        # Skip the final line:
        if line.startswith("Displayed ") or line.startswith(
            "Total number of prefixes "
        ):
            continue

        # Skip the heading info
        if skipping:
            if re.match(r"\s+Network\s+Next Hop\s+Metric.*", line):
                skipping = False
                continue
            else:
                continue

        """
        Sometimes router output is split over two lines
        *> 2001:200::/32    2001:504:24:1::1b1b:1
                                                    0             0 6939 2500 i

        *                   2001:504:24:1::1b1b:1
                                                    0             0 6939 42 i

        Sometimes it's split over three lines:
        *> 2001:200:900::/40
                            2001:504:24:1::1b1b:1
                                                    0             0 6939 2516 7660 7660 7660 i
        
        In this case we need to reconstruct into a single line
        """
        if len(line.split()) <= 3:
            split_lines.append(line)
            append_next = True
            continue

        """
        Assume the last line is the line with the AS path so we don't need to
        concat any more lines together after this
        """
        if append_next:
            split_lines.append(line)
            append_next = False

        if split_lines:
            line = ''.join(split_lines)
            split_lines = []

        # The last character on each line is the Unknown/EGP/IGP origin flag:
        line = line.rstrip("?").rstrip("e").rstrip("i")

        """
        Some lines start with a space before the valid/best indications:
        " *> "
        Some lines have no leading space:
        "*> "
        Some lines are paths which are neither valid nor best:
        "                                                2620:171:3c::209                               0             0 42 i"
        """
        if "*" in line or ">" in line or "=" in line:
            line = line.lstrip()

        """
        Is this line the start of a new prefix entry?
        There are one or two optional chars (after lstrip()) at the start
        of each line, and one or two space chars after those optional chars,
        before the prefix; "* ", "*  ", "> ", ">  ", "*> ", "*>  "
        If there is a new prefix on this line, with or without these optional
        chars, the 5th char will NOT be a space char.
        """
        pfx_offset = 4
        if line[pfx_offset] != " ":
            # Some lines start with "*u " or "*= "
            new_prefix = line[2:].split()[0]

            if new_prefix == "":
                raise ValueError(
                    f"{os.getpid()}: Couldn't extract prefix from line: {line}"
                )

            """
            Some of the route collectors don't include the prefix mask in the
            output of IPv4 prefixes.

            For prefixes with a first octet < 192, the prefix is sometimes
            repeated on the next line with the mask:
            *> 191.40.0.0       206.108.236.30           0             0 6939 52320 7738 i
            *> 191.40.0.0/18    206.108.236.30           0             0 6939 52320 7738 i
            
            In this case, we can skip the line and hopefully get the prefix on
            the next line. It could be a /16, or /17, or /18, etc, so we can't
            guess, however, for prefixes with a first octet >= 192, these are
            always /24s. We can simply add "/24" in this.
            """
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.0$", new_prefix):
                if int(new_prefix.split(".")[0]) >= 192:
                    new_prefix = new_prefix + "/24"
                    print(
                        f"{os.getpid()}: Implicitly added '/24' to prefix: {new_prefix}"
                    )
                else:
                    print(
                        f"{os.getpid()}: Skipping line due to missing mask length: {line}"
                    )
                    continue

            try:
                ipaddress.ip_network(new_prefix)
            except ValueError as e:
                print(f"{os.getpid()}: Unable to parse prefix: {line}")
                raise e

            current_prefix = new_prefix

            """
            Skip iBGP prefixes.
            Next hop is 0.0.0.0 or ::, or no AS path.

             *> 69.166.10.0/24   0.0.0.0                  0         32768
             *> 2620:0:870::/48  ::                       0         32768
            """
            if re.search(r"\s0\.0\.0\.0\s", line) or re.search(
                r"\s::\s", line
            ):
                print(f"{os.getpid()}: Skipping iBGP prefix: {line}")
                continue

            """
            Skip paths with no AS path (iBGP paths)
            *  196.49.14.0/24                               196.201.2.126                                  0             0
            """
            if len(line[pfx_offset:].split()) < 5:
                print(f"{os.getpid()}: Skipping iBGP path: {line}")
                continue

        else:
            """
            Skip paths with no AS path (iBGP paths)
            *>                                              196.201.2.126                                  0             0
            """
            if len(line[pfx_offset:].split()) < 4:
                print(f"{os.getpid()}: Skipping iBGP path: {line}")
                continue

        """
        Parse the AS path on this line for the current_prefix,
        unless it's a default route
        """

        """
        Each ASN in the path has reachability to this prefix.
        If one of those ASNs is an ASN of interest, add the prefix to the list
        of prefixes the ASN of interest can reach.

        *  41.73.158.0/24                               196.201.2.18                                   0             0 37350 30988
                                                        196.201.2.6                                    0             0 35091 37350
        *  2001:500:a8::/48                             fe80::20c:29ff:fee8:a0d1                       0             0 42 21556
        """
        if line[pfx_offset] != " ":
            as_path = line[pfx_offset:].split()[3:]
        else:
            as_path = line[pfx_offset:].split()[2:]

        """
        De-dupe the AS path (remove prepends).

        Also, split atomic aggregates into individual ASNs (assume they are
        reachable):
        6939 1299 2711 14615 {36040,398053} -> 6939 1299 2711 14615 36040 398053
        This means the AS-path is not 100% accurate but atomic aggregates are
        pretty rare these days and decreasing further because AS-sets are being
        deprecated. It should make no noticeable difference to the overall stats
        produced. It idea here is just to record all ASNs reachable, even if
        the path length is mangled.
        """
        deduped_path: list[int] = []
        try:
            for entry in as_path:
                if "{" in entry or "}" in entry:
                    for sub_entry in entry.split(","):
                        asn = int(sub_entry.lstrip("{").rstrip("}"))
                        if asn not in deduped_path:
                            deduped_path.append(asn)
                else:
                    if int(entry) not in deduped_path:
                        deduped_path.append(int(entry))
        except Exception as e:
            print(
                f"{os.getpid()}:parse_rib_data_ios: "
                f"Couldn't parse AS path: {as_path}"
            )
            raise e

        # In case the weight is included in the AS path, this will be handled:
        for asn in cli_args.asns:
            if int(asn) in deduped_path:
                routes[int(asn)].add_prefix(
                    current_prefix,
                    deduped_path[deduped_path.index(int(asn)) :],
                )

        parsed_lines += 1

    print(f"{os.getpid()}: Parsed {parsed_lines} lines")
    return routes


def parse_rib_data_junos(raw_rib_data: str) -> dict[int, AsnRoutes]:
    """
    Parse each line of the RIB output and store the prefix against each ASN
    in the path.
    """

    routes: dict[int, AsnRoutes] = {
        int(asn): AsnRoutes(peer_as=int(asn), routes={})
        for asn in cli_args.asns
    }

    """
    Each file starts with a varying number of lines of text, which explains
    the "show" command output.

    The data starts on the line after the line with the following column
    headings: Prefix		  Nexthop	       MED     Lclpref    AS path"
    """
    skipping = True

    parsed_lines = 0

    for line in raw_rib_data.splitlines():

        # Skip blank lines
        if line.strip() == "":
            continue

        # Skip the heading info
        if skipping:
            if re.match(
                r".*Prefix\s+Nexthop\s+MED\s+Lclpref\s+AS path.*", line
            ):
                skipping = False
                continue
            else:
                continue

        """
        Each line in the output has 2 columns before the prefix:
        @ 1.0.4.0/24              X.X.X.X                           7473 6453 7545 38803 I
        """

        line = line[2:]

        # The last character on each line is the Unknown/EGP/IGP origin flag:
        line = line.rstrip("?").rstrip("E").rstrip("I")

        values = line.split()
        prefix = values[0]
        as_path = values[2:]

        try:
            ipaddress.ip_network(prefix)
        except ValueError as e:
            print(f"{os.getpid()}: Unable to parse prefix: {line}")
            raise e

        """
        Skip default routes
        """
        if prefix == "0.0.0.0/0" or prefix == "::/0":
            print(f"{os.getpid()}: Skipping default route: {line}")
            continue

        """
        De-dupe the AS path (remove prepends).

        Also, split atomic aggregates into individual ASNs (assume they are
        reachable):
        6939 1299 2711 14615 {36040,398053} -> 6939 1299 2711 14615 36040 398053
        This means the AS-path is not 100% accurate but atomic aggregates are
        pretty rare these days and decreasing further because AS-sets are being
        deprecated. It should make no noticeable difference to the overall stats
        produced. It idea here is just to record all ASNs reachable, even if
        the path length is mangled.
        """
        deduped_path: list[int] = []
        try:
            for entry in as_path:
                if "{" in entry or "}" in entry:
                    for sub_entry in entry.split(","):
                        asn = int(sub_entry.lstrip("{").rstrip("}"))
                        if asn not in deduped_path:
                            deduped_path.append(asn)
                else:
                    if int(entry) not in deduped_path:
                        deduped_path.append(int(entry))
        except Exception as e:
            print(
                f"{os.getpid()}:parse_rib_data_junos: "
                f"Couldn't parse AS path: {as_path}"
            )
            raise e

        for asn in cli_args.asns:
            if int(asn) in deduped_path:
                routes[int(asn)].add_prefix(
                    prefix, deduped_path[deduped_path.index(int(asn)) :]
                )

        parsed_lines += 1

    print(f"{os.getpid()}: Parsed {parsed_lines} lines")
    return routes


def parse_rib_data_mrt(filename: str) -> dict[int, AsnRoutes]:
    """
    Look through the routes in a MRT table dump.
    Find all prefixes from any of the ASNs in the ASN list,
    and build a list of prefixes reachable via each of these ASNs.
    """

    routes: dict[int, AsnRoutes] = {
        int(asn): AsnRoutes(peer_as=int(asn), routes={})
        for asn in cli_args.asns
    }

    mrt_entries = mrtparse.Reader(filename)
    # Assume the first entry is the peer table.
    next(mrt_entries)

    mrt_routes = 0

    try:
        for mrt_e in mrt_entries:
            mrt_routes += 1
            prefix = f"{mrt_e.data['prefix']}/{mrt_e.data['length']}"

            if prefix == "0.0.0.0/0" or prefix == "::/0":
                print(f"{os.getpid()}: Skipping default route: {mrt_e.data}")
                continue

            try:
                ipaddress.ip_network(prefix)
            except ValueError as e:
                print(f"{os.getpid()}: Unable to parse prefix: {mrt_e.data}")
                raise e

            as_path: list[str] = []
            for rib_entry in mrt_e.data["rib_entries"]:
                try:
                    for path_atr in rib_entry["path_attributes"]:
                        if path_atr["type"] == {2: "AS_PATH"}:
                            # length == 0 means iBGP route
                            if path_atr["length"] != 0:
                                as_path = path_atr["value"][0]["value"]
                            break
                except IndexError as e:
                    print(
                        f"{os.getpid()}: Couldn't get AS-path for prefix "
                        f"{prefix} from RIB entry in file {filename}:\n"
                        f"{rib_entry}"
                    )
                    raise e

                if not as_path:
                    print(f"{os.getpid()}: Skipping iBGP route: {mrt_e.data}")
                    continue

                next_hop = ""
                if mrt_e.data["subtype"] == {2: "RIB_IPV4_UNICAST"}:
                    try:
                        next_hop = [
                            path_atr["value"]
                            for path_atr in rib_entry["path_attributes"]
                            if path_atr["type"] == {3: "NEXT_HOP"}
                        ][0]
                    except IndexError as e:
                        print(
                            f"{os.getpid()}: Couldn't get next-hop for prefix "
                            f"{prefix} from RIB entry in file {filename}:\n"
                            f"{rib_entry}"
                        )
                        raise e
                elif mrt_e.data["subtype"] == {4: "RIB_IPV6_UNICAST"}:
                    try:
                        next_hops: list[str] = [
                            path_atr["value"]["next_hop"]
                            for path_atr in rib_entry["path_attributes"]
                            if path_atr["type"] == {14: "MP_REACH_NLRI"}
                        ][0]
                    except IndexError as e:
                        print(
                            f"{os.getpid()}: Couldn't get next-hop for prefix "
                            f"{prefix} from RIB entry in file {filename}:\n"
                            f"{rib_entry}"
                        )
                        raise e
                    for next_hop in next_hops[:]:
                        if next_hop.lower().startswith("fe80:"):
                            next_hops.remove(next_hop)
                    next_hop = next_hops[0]
                else:
                    raise ValueError(
                        f"{os.getpid()}: Unknown subtype in file {filename}: "
                        f"{mrt_e.data}"
                    )

                if next_hop == "0.0.0.0/0" or next_hop == "::/0":
                    print(f"{os.getpid()}: Skipping iBGP route: {mrt_e.data}")
                    continue

                if not next_hop:
                    raise ValueError(
                        f"{os.getpid()}: No next hop in file {filename}: "
                        f"{mrt_e.data}"
                    )

                """
                De-dupe the AS path (remove prepends)
                """
                deduped_path: list[int] = []
                try:
                    for entry in as_path:
                        if int(entry) not in deduped_path:
                            deduped_path.append(int(entry))
                except Exception as e:
                    print(
                        f"{os.getpid()}:parse_rib_data_mrt: in {filename}, "
                        f"couldn't parse AS path: {as_path}"
                    )
                    raise e

                for asn in cli_args.asns:
                    if int(asn) in deduped_path:
                        routes[int(asn)].add_prefix(
                            prefix,
                            deduped_path[deduped_path.index(int(asn)) :],
                        )

    except KeyError:
        # Sometimes the MRT files contain corrupt entries
        print(
            f"{os.getpid()}: Skipped unparsable entry in MRT file "
            f"{filename}:\n"
            f"{traceback.format_exc()}"
        )

    except EOFError:
        # Sometimes the MRT file is corrupt and we reach EOF early
        print(
            f"{os.getpid()}: Reached unexpected EOF in MRT file {filename}:\n"
            f"{traceback.format_exc()}"
        )

    print(f"{os.getpid()}: Total MRT routes parsed: {mrt_routes}")
    return routes


def parse_rib_data_routeros(raw_rib_data: str) -> dict[int, AsnRoutes]:
    """
    Parse each line of the RIB output and store the prefix against each ASN
    in the path.
    """

    routes: dict[int, AsnRoutes] = {
        int(asn): AsnRoutes(peer_as=int(asn), routes={})
        for asn in cli_args.asns
    }

    """
    Each file starts with a varying number of lines of text, which explains
    the "show" command output. Some collectors support RPKI and others don't
    for example, which causes the output length to vary.

    The data starts on the line after the line with the following column
    headings: DST-ADDRESS, BGP.AS-PATH"
    """
    skipping = True

    parsed_lines = 0

    for line in raw_rib_data.splitlines():

        # Skip blank lines
        if line.strip() == "":
            continue

        # Skip the heading info
        if skipping:
            if re.match(r".*DST-ADDRESS\s+BGP.AS-PATH.*", line):
                skipping = False
                continue
            else:
                continue

        """
        Lines start with a varying amount of flags, without whitespace between them:
        Ab   142.202.235.0/24   701,6939,14713
         b   142.202.244.0/24   701,174,398079

        All lines are having exactly three columns: flags, prefix, as-path
        """
        prefix = line.split()[1]
        as_path = line.split()[2].split(",")

        if prefix == "":
            raise ValueError(
                f"{os.getpid()}: Couldn't extract prefix from line: {line}"
            )

        if as_path == "":
            raise ValueError(
                f"{os.getpid()}: Couldn't extract AS-Path from line: {line}"
            )

        try:
            ipaddress.ip_network(prefix)
        except ValueError as e:
            print(f"{os.getpid()}: Unable to parse prefix: {line}")
            raise e

        """
        Skip default routes
        """
        if prefix == "0.0.0.0/0" or prefix == "::/0":
            print(f"{os.getpid()}: Skipping default route: {line}")
            continue

        """
        De-dupe the AS path (remove prepends).

        Also, split atomic aggregates into individual ASNs (assume they are
        reachable):
        6939 1299 2711 14615{36040,398053 -> 6939 1299 2711 14615 36040 398053
        This means the AS-path is not 100% accurate but atomic aggregates are
        pretty rare these days and decreasing further because AS-sets are being
        deprecated. It should make no noticeable difference to the overall stats
        produced. It idea here is just to record all ASNs reachable, even if
        the path length is mangled.
        """
        deduped_path: list[int] = []
        try:
            for entry in as_path:
                # RouterOS CLI output truncates long AS paths!
                if entry.endswith("..."):
                    continue
                if "{" in entry:
                    for sub_entry in entry.split("{"):
                        if int(sub_entry) not in deduped_path:
                            deduped_path.append(int(sub_entry))
                else:
                    if int(entry) not in deduped_path:
                        deduped_path.append(int(entry))
        except Exception as e:
            print(
                f"{os.getpid()}:parse_rib_data_routeros: "
                f"Couldn't parse AS path: {as_path}"
            )
            raise e

        for asn in cli_args.asns:
            if int(asn) in deduped_path:
                routes[int(asn)].add_prefix(
                    prefix, deduped_path[deduped_path.index(int(asn)) :]
                )

        parsed_lines += 1

    print(f"{os.getpid()}: Parsed {parsed_lines} lines")
    return routes


file_formats = {
    "bird": parse_rib_data_bird,
    "eos": parse_rib_data_eos,
    "ios": parse_rib_data_ios,
    "junos": parse_rib_data_junos,
    "routeros": parse_rib_data_routeros,
}


def main() -> None:
    parse_cli_args()
    parse_files()


if __name__ == "__main__":
    main()
