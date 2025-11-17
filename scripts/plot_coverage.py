#!/usr/bin/env python3

from __future__ import annotations

import argparse
import gzip
import math
import json
import os
from csv import DictReader

import plotly.graph_objects as go
import plotly.offline as po
from inc.globals import (
    COVERAGE_AS_CONE,
    COVERAGE_AS_HOP_COUNT_ASNS,
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
    PLOT_AS_CONE_COVERAGE,
    PLOT_AS_CONE_OVERLAP,
    PLOT_AS_CONE_VISIBLE,
    PLOT_AS_CONTINENT_BREAKDOWN,
    PLOT_AS_HOPS_COUNT,
    PLOT_AS_HOPS_WEIGHTED,
    PLOT_FIRST_HOP_ASNS,
    PLOT_FIRST_HOP_OVERLAP,
    PLOT_FIRST_HOP_UNIQUE,
    PLOT_IPV4_COVERAGE,
    PLOT_IPV6_COVERAGE,
    PLOT_PATH,
    PLOT_PEERINGS,
    PLOT_V4_COVERAGE,
    PLOT_V4_SHORTER_T1,
    PLOT_V6_COVERAGE,
    PLOT_V6_SHORTER_T1,
)
from plotly.subplots import make_subplots

cli_args: argparse.Namespace


class AsConeCoverage:
    asns_reachable: list[int]
    asns_reachable_pct: list[float]
    asns_n_reachable: list[int]
    asns_n_reachable_pct: list[float]
    cone_size: list[int]
    cone_pct: list[float]
    networks: list[str]
    overlap: list[list[int | None]]
    percent: list[list[float | None]]

    def __init__(
        self: AsConeCoverage,
        asns_reachable: list[int] = [],
        asns_reachable_pct: list[float] = [],
        asns_n_reachable: list[int] = [],
        asns_n_reachable_pct: list[float] = [],
        cone_size: list[int] = [],
        cone_pct: list[float] = [],
        networks: list[str] = [],
        overlap: list[list[int | None]] = [],
        percent: list[list[float | None]] = [],
    ):
        self.asns_reachable = asns_reachable
        self.asns_reachable_pct = asns_reachable_pct
        self.asns_n_reachable = asns_n_reachable
        self.asns_n_reachable_pct = asns_n_reachable_pct
        self.cone_size = cone_size
        self.cone_pct = cone_pct
        self.networks = networks
        self.overlap = overlap
        self.percent = percent

    @staticmethod
    def from_csv() -> AsConeCoverage:
        filename = os.path.join(COVERAGE_DATA_PATH, COVERAGE_AS_CONE)

        print(f"Loading {filename}")
        with open(filename) as f:
            csv_data = DictReader(f.readlines())

        obj = AsConeCoverage()

        for row in csv_data:
            obj.asns_reachable.append(
                int(row["ASNs Reachable Via Other Networks"])
            )
            obj.asns_reachable_pct.append(
                float(row["% ASNs Reachable Via Other Networks"])
            )
            obj.asns_n_reachable.append(
                int(row["ASNs Not Reachable Via Other Networks"])
            )
            obj.asns_n_reachable_pct.append(
                float(row["% ASNs Not Reachable Via Other Networks"])
            )
            obj.cone_size.append(int(row["AS Cone"]))
            obj.cone_pct.append(float(row["% of all ASNs"]))
            obj.networks.append(f"{row['ASN']} {row['Name']}")
            obj.overlap.append([])
            obj.percent.append([])
            for key in row.keys():
                if key.startswith("ASN Overlap "):
                    if row[key].upper() == "X":
                        obj.overlap[-1].append(None)
                        obj.percent[-1].append(None)
                    else:
                        obj.overlap[-1].append(int(row[key]))
                        obj.percent[-1].append(float(row[f"% {key}"]))

        return obj


class AsContinents:
    networks: list[str]
    connected_as_count: list[int]
    continents = [
        "Africa",
        "Asia",
        "Europe",
        "North America",
        "Oceania",
        "South America",
    ]
    continent_spread: list[list[int]]
    continent_spread_pct: list[list[float]]

    def __init__(
        self: AsContinents,
        networks: list[str] = [],
        connected_as_count: list[int] = [],
        continent_spread: list[list[int]] = [],
        continent_spread_pct: list[list[float]] = [],
    ):
        self.networks = networks
        self.connected_as_count = connected_as_count
        self.continent_spread = continent_spread
        self.continent_spread_pct = continent_spread_pct

    @staticmethod
    def from_csv() -> AsContinents:
        filename = os.path.join(
            COVERAGE_DATA_PATH, COVERAGE_CONTINENT_BREAKDOWN
        )

        print(f"Loading {filename}")
        with open(filename) as f:
            csv_data = DictReader(f.readlines())

        obj = AsContinents()

        for row in csv_data:
            obj.networks.append(f"{row['ASN']} {row['Name']}")
            obj.connected_as_count.append(int(row["Directly Connected ASNs"]))
            obj.continent_spread.append([])
            obj.continent_spread_pct.append([])
            for continent in AsContinents.continents:
                obj.continent_spread[-1].append(int(row[continent]))
                obj.continent_spread_pct[-1].append(
                    float(row[f"% {continent}"])
                )

        return obj


class AsHopCount:
    networks: list[str]
    mode_hop_count: list[int]
    weighted_hop_count: list[int]
    hop_counts: list[list[int | None]]
    hop_counts_pct: list[list[float | None]]

    def __init__(
        self: AsHopCount,
        networks: list[str] = [],
        mode_hop_count: list[int] = [],
        weighted_hop_count: list[int] = [],
        hop_counts: list[list[int | None]] = [],
        hop_counts_pct: list[list[float | None]] = [],
    ):
        self.networks = networks
        self.mode_hop_count = mode_hop_count
        self.weighted_hop_count = weighted_hop_count
        self.hop_counts = hop_counts
        self.hop_counts_pct = hop_counts_pct

    @staticmethod
    def from_csv() -> AsHopCount:
        filename = os.path.join(COVERAGE_DATA_PATH, COVERAGE_AS_HOP_COUNT_ASNS)

        print(f"Loading {filename}")
        with open(filename) as f:
            csv_data = DictReader(f.readlines())

        obj = AsHopCount()

        for row in csv_data:
            obj.networks.append(f"{row['ASN']} {row['Name']}")
            obj.mode_hop_count.append(int(row["Mode Hop Count"]))
            obj.weighted_hop_count.append(int(row["Weighted Hop Count"]))
            obj.hop_counts.append([])
            obj.hop_counts_pct.append([])
            for key in row.keys():
                try:
                    count = int(key)
                    if count == 0:
                        continue
                    if count > 10:
                        break
                    if row[key].upper() == "X":
                        obj.hop_counts[-1].append(None)
                        obj.hop_counts_pct[-1].append(None)
                    else:
                        obj.hop_counts[-1].append(int(row[key]))
                        obj.hop_counts_pct[-1].append(float(row[f"% {key}"]))
                except ValueError:
                    continue

        return obj


class IpCoverage:
    networks: list[str]
    asns: list[int]
    v4: list[float]
    v6: list[float]

    def __init__(
        self: IpCoverage,
        networks: list[str] = [],
        asns: list[int] = [],
        v4: list[float] = [],
        v6: list[float] = [],
    ):
        self.networks = networks
        self.asns = asns
        self.v4 = v4
        self.v6 = v6

    @staticmethod
    def from_csv() -> IpCoverage:
        filename = os.path.join(COVERAGE_DATA_PATH, COVERAGE_IP)

        print(f"Loading {filename}")
        with open(filename) as f:
            csv_data = DictReader(f.readlines())

        obj = IpCoverage()

        for row in csv_data:
            obj.networks.append(f"{row['ASN']} {row['Name']}")
            obj.v4.append(float(row["% On-Net v4 Space"]))
            obj.v6.append(float(row["% On-Net v6 Space"]))

        return obj


class PeeringOverlap:
    n_uniq_peer_count: list[int]
    n_uniq_peer_pct: list[float]
    networks: list[str]
    peer_asn_count: list[int]
    peer_asn_pct: list[float]
    peering_overlap_count: list[list[int | None]]
    peering_overlap_pct: list[list[float | None]]
    uniq_peer_count: list[int]
    uniq_peer_pct: list[float]

    def __init__(
        self: PeeringOverlap,
        n_uniq_peer_count: list[int] = [],
        n_uniq_peer_pct: list[float] = [],
        networks: list[str] = [],
        peer_asn_count: list[int] = [],
        peer_asn_pct: list[float] = [],
        peering_overlap_count: list[list[int | None]] = [],
        peering_overlap_pct: list[list[float | None]] = [],
        uniq_peer_count: list[int] = [],
        uniq_peer_pct: list[float] = [],
    ):
        self.n_uniq_peer_count = n_uniq_peer_count
        self.n_uniq_peer_pct = n_uniq_peer_pct
        self.networks = networks
        self.peer_asn_count = peer_asn_count
        self.peer_asn_pct = peer_asn_pct
        self.peering_overlap_count = peering_overlap_count
        self.peering_overlap_pct = peering_overlap_pct
        self.uniq_peer_count = uniq_peer_count
        self.uniq_peer_pct = uniq_peer_pct

    @staticmethod
    def from_csv() -> PeeringOverlap:
        filename = os.path.join(COVERAGE_DATA_PATH, COVERAGE_PEERING)

        print(f"Loading {filename}")
        with open(filename) as f:
            csv_data = DictReader(f.readlines())

        obj = PeeringOverlap()

        for row in csv_data:
            obj.n_uniq_peer_count.append(int(row["Non-Unique Peer ASNs"]))
            obj.n_uniq_peer_pct.append(float(row["% Non-Unique Peer ASNs"]))
            obj.networks.append(f"{row['ASN']} {row['Name']}")
            obj.peer_asn_count.append(int(row["Peer ASNs"]))
            obj.peer_asn_pct.append(float(row["% of all ASNs"]))
            obj.uniq_peer_count.append(int(row["Unique Peer ASNs"]))
            obj.uniq_peer_pct.append(float(row["% Unique Peer ASNs"]))

            obj.peering_overlap_count.append([])
            obj.peering_overlap_pct.append([])
            for key in row.keys():
                if key.startswith("Peering Overlap "):
                    if row[key].upper() == "X":
                        obj.peering_overlap_count[-1].append(None)
                    else:
                        obj.peering_overlap_count[-1].append(int(row[key]))
                elif key.startswith("% Peering Overlap "):
                    if row[key].upper() == "X":
                        obj.peering_overlap_pct[-1].append(None)
                    else:
                        obj.peering_overlap_pct[-1].append(float(row[key]))

        return obj


class PrefixCoverage:
    networks: list[str]
    covered_count: list[int]
    covered_pct: list[float]
    n_covered_count: list[int]
    n_covered_pct: list[float]

    def __init__(
        self: PrefixCoverage,
        networks: list[str] = [],
        covered_count: list[int] = [],
        covered_pct: list[float] = [],
        n_covered_count: list[int] = [],
        n_covered_pct: list[float] = [],
    ):
        self.networks = networks
        self.covered_count = covered_count
        self.covered_pct = covered_pct
        self.n_covered_count = n_covered_count
        self.n_covered_pct = n_covered_pct

    @staticmethod
    def from_csv(filename: str = COVERAGE_V4) -> PrefixCoverage:
        filename = os.path.join(COVERAGE_DATA_PATH, filename)

        print(f"Loading {filename}")
        with open(filename) as f:
            csv_data = DictReader(f.readlines())

        obj = PrefixCoverage([], [], [], [], [])

        for row in csv_data:
            obj.networks.append(f"{row['ASN']} {row['Name']}")
            obj.covered_count.append(int(row["Covered by Any Other Network"]))
            obj.covered_pct.append(
                float(row["% Covered by Any Other Network"])
            )
            obj.n_covered_count.append(
                int(row["Not Covered by Any Other Network"])
            )
            obj.n_covered_pct.append(
                float(row["% Not Covered by Any Other Network"])
            )

        return obj


class PrefixShorterT1:
    networks: list[str]
    t1: list[bool]
    shorter_count: list[int]
    shorter_pct: list[float]
    n_shorter_count: list[int]
    n_shorter_pct: list[float]

    def __init__(
        self: PrefixShorterT1,
        networks: list[str] = [],
        t1: list[bool] = [],
        shorter_count: list[int] = [],
        shorter_pct: list[float] = [],
        n_shorter_count: list[int] = [],
        n_shorter_pct: list[float] = [],
    ):
        self.networks = networks
        self.t1 = t1
        self.shorter_count = shorter_count
        self.shorter_pct = shorter_pct
        self.n_shorter_count = n_shorter_count
        self.n_shorter_pct = n_shorter_pct

    @staticmethod
    def from_csv(filename: str = COVERAGE_V4_SHORTER_T1) -> PrefixShorterT1:
        filename = os.path.join(COVERAGE_DATA_PATH, filename)

        print(f"Loading {filename}")
        with open(filename) as f:
            csv_data = DictReader(f.readlines())

        obj = PrefixShorterT1([], [], [], [], [], [])

        for row in csv_data:
            obj.networks.append(f"{row['ASN']} {row['Name']}")
            obj.t1.append(True if row["T1"] == "True" else False)
            obj.shorter_count.append(int(row["Shorter Paths via Any Tier 1"]))
            obj.shorter_pct.append(
                float(row["% Shorter Paths via Any Tier 1"])
            )
            obj.n_shorter_count.append(
                int(row["Not Shorter Paths via Any Tier 1"])
            )
            obj.n_shorter_pct.append(
                float(row["% Not Shorter Paths via Any Tier 1"])
            )

        return obj


class T1Peerings:
    networks: list[str]
    names: list[str]
    asns: list[int]
    t1: list[bool]
    count: list[int]
    peerings: list[list[bool | None]]

    def __init__(
        self: T1Peerings,
        networks: list[str] = [],
        names: list[str] = [],
        asns: list[int] = [],
        t1: list[bool] = [],
        count: list[int] = [],
        peerings: list[list[bool | None]] = [],
    ):
        self.networks = networks
        self.names = names
        self.asns = asns
        self.t1 = t1
        self.count = count
        self.peerings = peerings

    @staticmethod
    def from_csv() -> T1Peerings:
        filename = os.path.join(COVERAGE_DATA_PATH, COVERAGE_PEERINGS)

        print(f"Loading {filename}")
        with open(filename) as f:
            csv_data = DictReader(f.readlines())

        obj = T1Peerings()

        assert csv_data.fieldnames
        for fieldname in csv_data.fieldnames:
            try:
                asn = int(fieldname)
                obj.asns.append(asn)
            except ValueError:
                continue

        for row in csv_data:
            obj.networks.append(str(row["ASN"]))
            obj.names.append(str(row["Name"]))
            obj.t1.append(True if row["T1"] == "True" else False)
            obj.count.append(int(row["Count"]))
            obj.peerings.append([])
            for key in row.keys():
                try:
                    int(key)
                    if row[key].upper() == "X":
                        obj.peerings[-1].append(None)
                    else:
                        obj.peerings[-1].append(
                            True if row[key] == "True" else False
                        )
                except ValueError:
                    continue

        return obj


def load_global_stats() -> dict[str, list[int | str] | int]:
    filename = os.path.join(COVERAGE_DATA_PATH, COVERAGE_GLOBAL)
    print(f"Loading global stats from {filename}")
    with gzip.open(filename) as f:
        # orjson can't load >64bit int
        global_stats: dict = json.loads(f.read())

    global_stats["total_asns"] = len(global_stats["all_asns"])
    return global_stats


def plot_as_cone_coverage(data: AsConeCoverage, global_asn_count: int) -> None:
    sorted_data = sorted(
        list(zip(data.networks, data.cone_size, data.cone_pct, strict=False)),
        key=lambda x: x[1],
        reverse=True,
    )

    fig = go.Figure(
        data=[
            go.Bar(
                y=[x[1] for x in sorted_data],
                x=[x[0] for x in sorted_data],
                name="Visible ASNs",
                marker={"color": "cornflowerblue"},
                text=[x[1] for x in sorted_data],
                customdata=[x[1] for x in sorted_data],
                hovertemplate="%{customdata}",
                yaxis="y1",
            ),
            go.Scatter(
                y=[x[2] for x in sorted_data],
                x=[x[0] for x in sorted_data],
                name="% of all ASNs in DFZ",
                marker={"color": "crimson"},
                line={"width": 3},
                customdata=[x[2] for x in sorted_data],
                hovertemplate="%{customdata}",
                yaxis="y2",
            ),
        ],
        layout={
            "yaxis": {"title": "Visible ASNs"},
            "yaxis2": {
                "title": "% of all ASNs in DFZ",
                "overlaying": "y",
                "side": "right",
            },
        },
    )
    fig.update_layout(
        barmode="group",
        title_text=(
            f"Visibility of All ASNs Seen in The DFZ ({global_asn_count})"
        ),
        title_x=0.5,
        xaxis_title_text="Network",
        yaxis_range=[
            min(data.cone_size) - int(min(data.cone_size) * 0.02),
            global_asn_count,
        ],
        legend=dict(yanchor="top", xanchor="left", x=0.01, y=1.1),
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_AS_CONE_COVERAGE),
        auto_open=False,
    )


def plot_as_cone_overlap(data: AsConeCoverage) -> None:
    values: list[list[float | str]] = []
    for col in data.percent:
        values.append([])
        for val in col:
            if val:
                values[-1].append(val)
            else:
                values[-1].append("")

    fig = make_subplots()
    fig.add_trace(
        go.Heatmap(
            z=values,
            text=values,
            x=data.networks,
            y=data.networks,
            texttemplate="%{text}",
            customdata=data.overlap,
            hovertemplate="%{customdata} ASNs",
            name="",
        )
    )
    fig.update_layout(
        title_text="% of ASN Visibility Overlap",
        title_x=0.5,
        xaxis={"side": "bottom"},
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_AS_CONE_OVERLAP),
        auto_open=False,
    )


def plot_as_cone_visible(data: AsConeCoverage) -> None:
    fig = go.Figure(
        data=[
            go.Bar(
                name="Visible",
                x=data.networks,
                y=data.asns_reachable_pct,
                text=data.asns_reachable_pct,
                customdata=data.asns_reachable,
                hovertemplate="%{customdata} ASNs",
                yaxis="y1",
                offsetgroup=1,
            ),
            go.Bar(
                name="Not Visible",
                x=data.networks,
                y=data.asns_n_reachable_pct,
                text=data.asns_n_reachable_pct,
                customdata=data.asns_n_reachable,
                hovertemplate="%{customdata} ASNs",
                yaxis="y2",
                offsetgroup=2,
            ),
        ],
        layout={
            "yaxis": {"title": "% ASNs Visible via Other Networks"},
            "yaxis2": {
                "title": "% ASNs Not Visible via Other Networks",
                "overlaying": "y",
                "side": "right",
            },
        },
    )
    fig.update_layout(
        barmode="group",
        title_text="% of Visible ASNs (Not-)Visible via Other Networks",
        title_x=0.5,
        legend=dict(yanchor="top", xanchor="left", x=0.01, y=1.1),
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_AS_CONE_VISIBLE),
        auto_open=False,
    )


def plot_as_hops_weighted(data: AsHopCount) -> None:
    sorted_data = sorted(
        list(
            zip(
                data.networks,
                data.weighted_hop_count,
                data.mode_hop_count,
                strict=False,
            )
        ),
        key=lambda x: x[1],
        reverse=True,
    )

    fig = go.Figure(
        data=[
            go.Bar(
                name="Weighted Hop Count",
                x=[x[0] for x in sorted_data],
                y=[x[1] for x in sorted_data],
                text=[x[1] for x in sorted_data],
                customdata=[x[1] for x in sorted_data],
                hovertemplate="%{customdata}",
                yaxis="y1",
                offsetgroup=1,
            ),
            go.Bar(
                name="Mode Hop Count",
                x=[x[0] for x in sorted_data],
                y=[x[2] for x in sorted_data],
                text=[x[2] for x in sorted_data],
                customdata=[x[2] for x in sorted_data],
                hovertemplate="%{customdata}",
                yaxis="y2",
                offsetgroup=2,
            ),
        ],
        layout={
            "yaxis": {"title": "Weighted Hop Count (higher is better)"},
            "yaxis2": {
                "title": "Mode Hop Count (lower is better)",
                "overlaying": "y",
                "side": "right",
            },
        },
    )
    fig.update_layout(
        barmode="group",
        title_text="Weighted AS Hop Count (To ASNs <= 10 Hops Away)",
        title_x=0.5,
        legend=dict(yanchor="top", xanchor="left", x=0.01, y=1.1),
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_AS_HOPS_WEIGHTED),
        auto_open=False,
    )


def plot_as_hops_count(data: AsHopCount) -> None:
    values: list[list[float | str]] = []
    for col in data.hop_counts_pct:
        values.append([])
        for val in col:
            if isinstance(val, float):
                values[-1].append(val)
            else:
                values[-1].append("")

    fig = make_subplots()
    fig.add_trace(
        go.Heatmap(
            z=values,
            text=values,
            x=[x for x in range(1, 11)],
            y=data.networks,
            texttemplate="%{text}",
            customdata=data.hop_counts,
            hovertemplate="%{customdata} ASNs",
            name="",
        )
    )
    fig.update_layout(
        title_text="AS Hop Count Frequency (<= 10 hops)",
        title_x=0.5,
        xaxis={
            "side": "bottom",
            "dtick": 1,
            "title": "% of ASNs reachable by hop count",
        },
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_AS_HOPS_COUNT),
        auto_open=False,
    )


def plot_as_continents(data: AsContinents) -> None:
    labels = data.continents
    cols = 7
    rows = math.ceil(len(data.networks) / cols)

    # Create subplots: use 'domain' type for Pie subplot
    fig = make_subplots(
        rows=rows,
        cols=cols,
        specs=[[{'type': 'domain'} for _ in range(cols)] for _ in range(rows)],
    )
    """
    {
        "domain": {
            "x":[0.38437499999999997,0.48749999999999993],
            "y":[0.848,1.0]
        },
        hole":0.4,
        hoverinfo":"label+percent+name",
        "labels":["Africa","Asia","Europe","North America","Oceania","South America"]
        "name":"2914 NTT",
        "values":[0.92,22.26,30.07,41.3,2.09,3.37],
        "type":"pie"
    }
    """

    annotations = []
    for i in range(0, len(data.networks)):
        fig_row = (i // cols) + 1
        fig_col = (i % cols) + 1

        fig.add_trace(
            go.Pie(
                labels=labels,
                values=data.continent_spread[i],
                name=data.networks[i],
            ),
            fig_row,
            fig_col,
        )

        # Add annotations in the center of the donut pies.
        annotation_x = sum(fig.get_subplot(fig_row, fig_col).x) / 2
        annotation_y = sum(fig.get_subplot(fig_row, fig_col).y) / 2

        # We have to offset the Y value base on the row
        if rows % 2 == 0:
            # even
            mid = rows / 2
        else:
            # odd
            mid = math.ceil(rows / 2)

        if fig_row < mid:
            diff = -(mid - 1) * 0.01
        elif fig_row == mid:
            diff = 0
        elif fig_row > mid:
            diff = (mid - 1) * 0.01

        annotation_y = annotation_y - diff

        annotations.append(
            dict(
                text=data.networks[i].replace(" ", "<br>"),
                x=annotation_x,
                y=annotation_y,
                font_size=10,
                showarrow=False,
                xanchor="center",
            )
        )
    # Use `hole` to create a donut-like pie chart
    fig.update_traces(hole=0.4, hoverinfo="label+value")

    fig.update_layout(
        title_text="Breakdown of Directly Connect ASNs by Continent",
        title_x=0.5,
        annotations=annotations,
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_AS_CONTINENT_BREAKDOWN),
        auto_open=False,
    )


def plot_ipv4_coverage(data: IpCoverage, global_ip_addrs: int) -> None:
    sorted_data = sorted(
        list(zip(data.networks, data.v4, strict=False)),
        key=lambda x: x[1],
        reverse=True,
    )

    fig = go.Figure(
        data=[
            go.Bar(
                y=[x[1] for x in sorted_data],
                x=[x[0] for x in sorted_data],
                name="% Visible",
                marker={"color": "cornflowerblue"},
                text=[x[1] for x in sorted_data],
                customdata=[x[1] for x in sorted_data],
                hovertemplate="%{customdata}",
                yaxis="y1",
            )
        ],
        layout={"yaxis": {"title": "%"}},
    )
    fig.update_layout(
        barmode="group",
        title_text=(
            f"% of All Announced v4 Address Space ({global_ip_addrs:,} IPs) "
            "Visible via Each Network"
        ),
        title_x=0.5,
        xaxis_title_text="Network",
        yaxis_range=[min(data.v4) - int(min(data.v4) * 0.1), max(data.v4)],
        legend=dict(yanchor="top", xanchor="left", x=0.01, y=1.05),
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_IPV4_COVERAGE),
        auto_open=False,
    )


def plot_ipv6_coverage(data: IpCoverage, global_ip_addrs: int) -> None:
    sorted_data = sorted(
        list(zip(data.networks, data.v6, strict=False)),
        key=lambda x: x[1],
        reverse=True,
    )

    fig = go.Figure(
        data=[
            go.Bar(
                y=[x[1] for x in sorted_data],
                x=[x[0] for x in sorted_data],
                name="% Reachable",
                marker={"color": "cornflowerblue"},
                text=[x[1] for x in sorted_data],
                customdata=[x[1] for x in sorted_data],
                hovertemplate="%{customdata}",
                yaxis="y1",
            )
        ],
        layout={"yaxis": {"title": "%"}},
    )

    # This is fine ¯\_(ツ)_/¯
    global_ip_addrs_str = f"{global_ip_addrs:f}".split(".")[0]
    global_ip_addrs_str = ",".join(
        [
            global_ip_addrs_str[x : x + 3]
            for x in range(0, len(global_ip_addrs_str), 3)
        ]
    )

    fig.update_layout(
        barmode="group",
        title_text=(
            f"% of All Announced v6 Address Space ({global_ip_addrs_str} IPs) "
            "Visible via Each Network"
        ),
        title_x=0.5,
        xaxis_title_text="Network",
        yaxis_range=[min(data.v6) - int(min(data.v6) * 0.1), max(data.v6)],
        legend=dict(yanchor="top", xanchor="left", x=0.01, y=1.05),
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_IPV6_COVERAGE),
        auto_open=False,
    )


def plot_peering_direct(data: PeeringOverlap, global_asn_count: int) -> None:
    sorted_data = sorted(
        list(
            zip(
                data.networks,
                data.peer_asn_count,
                data.peer_asn_pct,
                strict=False,
            )
        ),
        key=lambda x: x[1],
        reverse=True,
    )

    fig = go.Figure(
        data=[
            go.Bar(
                y=[x[1] for x in sorted_data],
                x=[x[0] for x in sorted_data],
                name="Visible ASNs",
                marker={"color": "cornflowerblue"},
                text=[x[1] for x in sorted_data],
                customdata=[x[1] for x in sorted_data],
                hovertemplate="%{customdata}",
                yaxis="y1",
            ),
            go.Scatter(
                y=[x[2] for x in sorted_data],
                x=[x[0] for x in sorted_data],
                name="% of all ASNs in DFZ",
                marker={"color": "crimson"},
                line={"width": 3},
                customdata=[x[2] for x in sorted_data],
                hovertemplate="%{customdata}",
                yaxis="y2",
            ),
        ],
        layout={
            "yaxis": {"title": "Directly Connected ASNs"},
            "yaxis2": {
                "title": "% of all ASNs in DFZ",
                "overlaying": "y",
                "side": "right",
            },
        },
    )
    fig.update_layout(
        barmode="group",
        title_text=(
            f"% of All ASNs Seen in The DFZ ({global_asn_count}) Which Are "
            f"Directly Connected"
        ),
        title_x=0.5,
        xaxis_title_text="Network",
        yaxis_range=[
            min(data.peer_asn_count) - int(min(data.peer_asn_count) * 0.02),
            max(data.peer_asn_count),
        ],
        legend=dict(yanchor="top", xanchor="left", x=0.01, y=1.1),
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_FIRST_HOP_ASNS),
        auto_open=False,
    )


def plot_peering_overlap(data: PeeringOverlap) -> None:
    percentages: list[list[float | str]] = []
    for col in data.peering_overlap_pct:
        percentages.append([])
        for val in col:
            if val:
                percentages[-1].append(val)
            else:
                percentages[-1].append("")

    fig = make_subplots()
    fig.add_trace(
        go.Heatmap(
            z=percentages,
            text=percentages,
            x=data.networks,
            y=data.networks,
            texttemplate="%{text}",
            customdata=data.peering_overlap_count,
            hovertemplate="%{customdata} ASNs",
            name="",
        )
    )
    fig.update_layout(
        title_text="% of Overlapping Direct Peers",
        title_x=0.5,
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_FIRST_HOP_OVERLAP),
        auto_open=False,
    )


def plot_peering_unique(data: PeeringOverlap) -> None:
    sorted_data = sorted(
        list(
            zip(
                data.networks,
                data.uniq_peer_count,
                data.n_uniq_peer_count,
                strict=False,
            )
        ),
        key=lambda x: x[1],
        reverse=False,
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=[x[0] for x in sorted_data],
            x=[x[1] for x in sorted_data],
            name="Unique Frist Hop ASNs",
            orientation="h",
            customdata=[x[1] for x in sorted_data],
            hovertemplate="%{customdata}",
        )
    )
    fig.add_trace(
        go.Bar(
            y=[x[0] for x in sorted_data],
            x=[x[2] for x in sorted_data],
            name="Non-Unique First Hop Asns",
            orientation="h",
            customdata=[x[2] for x in sorted_data],
            hovertemplate="%{customdata}",
        )
    )

    fig.update_layout(
        barmode="stack",
        title_text=("(Non-)Unique Directly Connected ASNs"),
        title_x=0.5,
        xaxis_title="ASN Count",
        legend=dict(yanchor="top", xanchor="left", x=0.01, y=1.1),
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_FIRST_HOP_UNIQUE),
        auto_open=False,
    )


def plot_peerings(data: T1Peerings) -> None:
    text_colour_map = {True: "darkgreen", False: "firebrick", None: "black"}
    fill_colour_map = {
        True: "#e0f3f8",
        False: "lightgoldenrodyellow",
        None: "white",
    }

    headings = ["<b>ASN</b>", "<b>Name</b>", "<b>Count</b>"] + [
        f"<b>{asn}</b>" for asn in data.asns
    ]

    # The values are column values now row values
    values: list[list[str]] = []
    values.append(data.networks)
    values.append(data.names)
    values.append([str(count) for count in data.count])

    fill_colours: list[list[str]] = []
    fill_colours.append([fill_colour_map[None]] * len(data.networks))
    fill_colours.append([fill_colour_map[None]] * len(data.names))
    fill_colours.append([fill_colour_map[None]] * len(data.count))

    text_colours: list[list[str]] = []
    text_colours.append([text_colour_map[None]] * len(data.networks))
    text_colours.append([text_colour_map[None]] * len(data.names))
    text_colours.append([text_colour_map[None]] * len(data.count))

    for col in range(len(data.asns)):
        values.append([])
        fill_colours.append([])
        text_colours.append([])

        for row in range(len(data.networks)):
            val = data.peerings[row][col]

            if isinstance(val, bool):
                values[-1].append(str(val))
            else:
                values[-1].append("N/A")

            text_colours[-1].append(text_colour_map[val])

            if val == None:
                fill_colours[-1].append(fill_colour_map[val])
                continue

            is_t1: bool | None
            if col < len(data.t1):
                is_t1 = data.t1[col] and data.t1[row]
            else:
                is_t1 = False
            fill_colours[-1].append(fill_colour_map[is_t1])

    fig = go.Figure(
        data=[
            go.Table(
                header=dict(
                    values=headings,
                    line_color='gainsboro',
                    fill_color='white',
                    align='center',
                    font=dict(color='black', size=12),
                ),
                cells=dict(
                    values=values,
                    line_color='gainsboro',
                    fill_color=fill_colours,
                    align='center',
                    font=dict(color=text_colours, size=12),
                ),
            )
        ]
    )

    fig.update_layout(
        title_text="Peering Matrix",
        title_x=0.5,
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    fig.update_layout(width=2560)
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, PLOT_PEERINGS),
        auto_open=False,
    )


def plot_prefix_coverage(
    data: PrefixCoverage, filename: str, family: int
) -> None:
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=data.networks,
            x=data.n_covered_pct,
            name="% Prefixes Not Visible by Other Networks",
            orientation="h",
            customdata=data.n_covered_pct,
            hovertemplate="%{customdata}",
        )
    )
    fig.add_trace(
        go.Bar(
            y=data.networks,
            x=data.covered_pct,
            name="% Prefixes Visible by Other Networks",
            orientation="h",
            customdata=data.covered_pct,
            hovertemplate="%{customdata}",
        )
    )

    fig.update_layout(
        barmode="stack",
        title_text=f"% of v{family} Prefixes (Not-)Visible by Other Networks",
        title_x=0.5,
        legend=dict(yanchor="top", xanchor="left", x=0.01, y=1.1),
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, filename),
        auto_open=False,
    )


def plot_prefix_prefer_t1(
    data: PrefixShorterT1, filename: str, family: int
) -> None:
    sorted_data = sorted(
        list(
            zip(
                data.networks,
                data.shorter_count,
                data.shorter_pct,
                data.n_shorter_count,
                data.n_shorter_pct,
                strict=False,
            )
        ),
        key=lambda x: x[4],
        reverse=False,
    )

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=[x[0] for x in sorted_data],
            x=[x[4] for x in sorted_data],
            name="Prefixes with Fewer Hops Not via Any Tier 1",
            orientation="h",
            customdata=[f"{x[4]}% ({x[3]})" for x in sorted_data],
            hovertemplate="%{customdata}",
        )
    )
    fig.add_trace(
        go.Bar(
            y=[x[0] for x in sorted_data],
            x=[x[2] for x in sorted_data],
            name="Prefixes with Fewer Hops via Any Tier 1",
            orientation="h",
            customdata=[f"{x[2]}% ({x[1]})" for x in sorted_data],
            hovertemplate="%{customdata}",
        )
    )

    fig.update_layout(
        barmode="stack",
        title_text=(
            f"v{family} Prefixes where Fewest AS Hops Is (Not) via Any Tier 1"
        ),
        title_x=0.5,
        xaxis_title="Prefix Percentage",
        legend=dict(yanchor="top", xanchor="left", x=0.01, y=1.1),
        margin=dict(l=0, r=0, b=0, t=100, pad=0),
    )
    po.plot(
        fig,
        image_width=1920,
        image_height=1080,
        filename=os.path.join(PLOT_PATH, filename),
        auto_open=False,
    )


def parse_cli_args() -> None:
    parser = argparse.ArgumentParser(
        description="Script to plot network coverage data",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-input",
        help="Path to input directory of AsStats files",
        type=str,
        metavar="path",
        default=COVERAGE_DATA_PATH,
    )
    parser.add_argument(
        "-output",
        help="Path to store generated charts/plots",
        type=str,
        metavar="path",
        default=PLOT_PATH,
    )

    global cli_args
    cli_args = parser.parse_args()


def main() -> None:
    """
    Plotly colours:
    https://masamasace.github.io/plotly_color/
    https://plotly.com/python/css-colors/
    https://plotly.com/python/builtin-colorscales/
    """

    parse_cli_args()
    os.makedirs(PLOT_PATH, exist_ok=True)

    global_stats = load_global_stats()
    assert isinstance(global_stats["total_asns"], int)
    assert isinstance(global_stats["v4_ips"], int)
    assert isinstance(global_stats["v6_ips"], int)

    as_coverage = AsConeCoverage.from_csv()
    plot_as_cone_visible(as_coverage)
    plot_as_cone_coverage(as_coverage, global_stats["total_asns"])
    plot_as_cone_overlap(as_coverage)
    as_hops = AsHopCount.from_csv()
    plot_as_hops_weighted(as_hops)
    plot_as_hops_count(as_hops)
    as_continents = AsContinents.from_csv()
    plot_as_continents(as_continents)
    t1_peerings = T1Peerings.from_csv()
    plot_peerings(t1_peerings)
    ip_coverage = IpCoverage.from_csv()
    plot_ipv4_coverage(ip_coverage, global_stats["v4_ips"])
    plot_ipv6_coverage(ip_coverage, global_stats["v6_ips"])
    peering_overlap = PeeringOverlap.from_csv()
    plot_peering_direct(peering_overlap, global_stats["total_asns"])
    plot_peering_unique(peering_overlap)
    plot_peering_overlap(peering_overlap)
    v4_coverage = PrefixCoverage.from_csv()
    v6_coverage = PrefixCoverage.from_csv(COVERAGE_V6)
    plot_prefix_coverage(v4_coverage, PLOT_V4_COVERAGE, 4)
    plot_prefix_coverage(v6_coverage, PLOT_V6_COVERAGE, 6)
    v4_shorter_t1 = PrefixShorterT1.from_csv()
    v6_shorter_t1 = PrefixShorterT1.from_csv(COVERAGE_V6_SHORTER_T1)
    plot_prefix_prefer_t1(v4_shorter_t1, PLOT_V4_SHORTER_T1, 4)
    plot_prefix_prefer_t1(v6_shorter_t1, PLOT_V6_SHORTER_T1, 6)


if __name__ == "__main__":
    main()
