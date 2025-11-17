from __future__ import annotations

from typing import Optional

from .data_sources import Collectors


class Asn:
    asn: int
    collector: Optional[Collectors.Collector]
    tier_1: bool
    name: str
    known_upstreams: set[int]

    def __init__(
        self: Asn,
        asn: int,
        collector: Optional[Collectors.Collector],
        tier_1: bool,
        name: str,
        known_upstreams: set[int],
    ):
        self.asn = asn
        self.collector = collector
        self.tier_1 = tier_1
        self.name = name
        self.known_upstreams = known_upstreams


asns = {
    # Tier 1 ASNs
    174: Asn(
        asn=174,
        collector=Collectors.Collector.RRC_25,
        tier_1=True,
        name="Cogent",
        known_upstreams=set(),
    ),
    701: Asn(
        asn=701,
        collector=None,
        tier_1=True,
        name="Verizon",
        known_upstreams=set(),
    ),
    1299: Asn(
        asn=1299,
        collector=Collectors.Collector.RRC_01,
        tier_1=True,
        name="Telia",
        known_upstreams=set(),
    ),
    2914: Asn(
        asn=2914,
        collector=Collectors.Collector.RRC_01,
        tier_1=True,
        name="NTT",
        known_upstreams=set(),
    ),
    3257: Asn(
        asn=3257,
        collector=Collectors.Collector.RRC_01,
        tier_1=True,
        name="GTT",
        known_upstreams=set(),
    ),
    3320: Asn(
        asn=3320,
        collector=Collectors.Collector.RRC_01,
        tier_1=True,
        name="DTAG",
        known_upstreams=set(),
    ),
    3356: Asn(
        asn=3356,
        collector=None,
        tier_1=True,
        name="Lumen",
        known_upstreams=set(),
    ),
    3491: Asn(
        asn=3491,
        collector=Collectors.Collector.RRC_01,
        tier_1=True,
        name="PCCW",
        known_upstreams=set(),
    ),
    5511: Asn(
        asn=5511,
        collector=Collectors.Collector.RRC_01,
        tier_1=True,
        name="Orange",
        known_upstreams=set(),
    ),
    6453: Asn(
        asn=6453,
        collector=Collectors.Collector.RRC_03,
        tier_1=True,
        name="Tata",
        known_upstreams=set(),
    ),
    6461: Asn(
        asn=6461,
        collector=Collectors.Collector.RRC_01,
        tier_1=True,
        name="Zayo",
        known_upstreams=set(),
    ),
    6762: Asn(
        asn=6762,
        collector=Collectors.Collector.RRC_12,
        tier_1=True,
        name="TI Sparkle",
        known_upstreams=set(),
    ),
    6939: Asn(
        asn=6939,
        collector=Collectors.Collector.RRC_01,
        tier_1=True,
        name="Hurricane Electric",
        known_upstreams=set(),
    ),
    6830: Asn(
        asn=6830,
        collector=Collectors.Collector.RRC_01,
        tier_1=True,
        name="Liberty Global",
        known_upstreams=set(),
    ),
    7018: Asn(
        asn=7018,
        collector=Collectors.Collector.RRC_00,
        tier_1=True,
        name="AT&T",
        known_upstreams=set(),
    ),
    12956: Asn(
        asn=12956,
        collector=Collectors.Collector.RRC_03,
        tier_1=True,
        name="Telxius",
        known_upstreams=set(),
    ),
    # Tier 2 ASNs with the most peers
    2635: Asn(
        asn=2635,
        collector=None,
        tier_1=False,
        name="Automattic",
        known_upstreams=set([1299, 2914, 3356]),
    ),
    9498: Asn(
        asn=9498,
        collector=None,
        tier_1=False,
        name="Bharti Airtel",
        known_upstreams=set(
            [174, 1299, 2914, 3257, 3491, 3356, 6461, 6762, 6939]
        ),
    ),
    13335: Asn(
        asn=13335,
        collector=None,
        tier_1=False,
        name="Cloudflare",
        known_upstreams=set(
            [174, 1299, 2914, 3257, 3491, 3356, 6453, 6461, 6762, 12956]
        ),
    ),
    14840: Asn(
        asn=14840,
        collector=Collectors.Collector.RRC_25,
        tier_1=False,
        name="BR DIGITAL",
        known_upstreams=set([174, 3356, 6762]),
    ),
    20473: Asn(
        asn=20473,
        collector=None,
        tier_1=False,
        name="Constant Company",
        known_upstreams=set([174, 1299, 2914, 3257, 3356, 3491, 6762, 6936]),
    ),
    24482: Asn(
        asn=24482,
        collector=Collectors.Collector.RRC_00,
        tier_1=False,
        name="SG.GS",
        known_upstreams=set([2914, 3491, 6453]),
    ),
    35280: Asn(
        asn=35280,
        collector=Collectors.Collector.RRC_15,
        tier_1=False,
        name="F5 Networks",
        known_upstreams=set([1299, 2914, 3356, 6453, 12956]),
    ),
    36236: Asn(
        asn=36236,
        collector=Collectors.Collector.RRC_25,
        tier_1=False,
        name="Net Actuate",
        known_upstreams=set([174, 1299, 2914, 3257, 3356, 3491, 6762, 6939]),
    ),
    37721: Asn(
        asn=37721,
        collector=None,
        tier_1=False,
        name="VT&S",
        known_upstreams=set(
            [
                174,
                1299,
                2914,
                3257,
                3329,
                3356,
                5511,
                6453,
                6461,
                6762,
                6830,
                6939,
                12956,
            ]
        ),
    ),
    39120: Asn(
        asn=39120,
        collector=Collectors.Collector.ROUTEVIEWS_AMSIX,
        tier_1=False,
        name="Convergenze",
        known_upstreams=set([174, 3257, 3356, 6939]),
    ),
    49544: Asn(
        asn=49544,
        collector=Collectors.Collector.RRC_00,
        tier_1=False,
        name="i3D.net",
        known_upstreams=set([174, 1299, 2914, 3356, 12956]),
    ),
    57463: Asn(
        asn=57463,
        collector=None,
        tier_1=False,
        name="NetIX Comms",
        known_upstreams=set([3356, 5511, 6936]),
    ),
    64289: Asn(
        asn=64289,
        collector=Collectors.Collector.ROUTEVIEWS_SFMIX,
        tier_1=False,
        name="Macarne",
        known_upstreams=set(
            [174, 1299, 2914, 3257, 3320, 5511, 6453, 6762, 12956]
        ),
    ),
    199524: Asn(
        asn=199524,
        collector=Collectors.Collector.RRC_03,
        tier_1=False,
        name="G-Core",
        known_upstreams=set(
            [
                174,
                1299,
                2914,
                3257,
                3320,
                3356,
                3491,
                5511,
                6453,
                6762,
                6830,
                6939,
                12956,
            ]
        ),
    ),
    # Tier 2 ASNs with the largest AS cone
    1273: Asn(
        asn=1273,
        collector=None,
        tier_1=False,
        name="Vodafone",
        known_upstreams=set([174, 701, 1299, 2914, 3356, 6453, 12956]),
    ),
    4637: Asn(
        asn=4637,
        collector=None,
        tier_1=False,
        name="Telstra",
        known_upstreams=set([174, 1299, 2914, 3356, 6453, 6461, 12956]),
    ),
    7195: Asn(
        asn=7195,
        collector=None,
        tier_1=False,
        name="EdgeUno",
        known_upstreams=set([174, 1299, 3257, 3356]),
    ),
    7473: Asn(
        asn=7473,
        collector=None,
        tier_1=False,
        name="SingTel",
        known_upstreams=set([1299, 3356, 6453, 6461, 6939]),
    ),
    9002: Asn(
        asn=9002,
        collector=Collectors.Collector.RRC_01,
        tier_1=False,
        name="RETN",
        known_upstreams=set([1299, 3320, 3356, 3491, 6453, 6762, 12956]),
    ),
    # 9498 Bharti Airtel - already included
    12389: Asn(
        asn=12389,
        collector=None,
        tier_1=False,
        name="Rostelecom",
        known_upstreams=set([174, 1299, 3257, 3491, 5511, 6762, 6939]),
    ),
    13786: Asn(
        asn=13786,
        collector=Collectors.Collector.RRC_15,
        tier_1=False,
        name="Seaborn",
        known_upstreams=set([174, 2914, 3356, 6939]),
    ),
    23911: Asn(
        asn=23911,
        collector=None,
        tier_1=False,
        name="CNGI BJIX",
        known_upstreams=set([6939]),
    ),
    37468: Asn(
        asn=37468,
        collector=Collectors.Collector.ROUTEVIEWS_NAPAFRICA,
        tier_1=False,
        name="Angola Cables",
        known_upstreams=set([174, 1299, 2914, 3257, 3356, 6453, 12956]),
    ),
    38255: Asn(
        asn=38255,
        collector=None,
        tier_1=False,
        name="CERNET",
        known_upstreams=set([]),
    ),
    52320: Asn(
        asn=52320,
        collector=Collectors.Collector.RRC_16,
        tier_1=False,
        name="GlobeNet",
        known_upstreams=set([174, 1299, 2914, 3356, 6461, 6939, 12956]),
    ),
}


def skip_asn(asn: int) -> bool:
    """
    Returns True if this is not an ASN of interest
    """
    return asn not in asns


def is_tier1(asn: int) -> bool:
    if asn not in asns:
        return False
    return asns[asn].tier_1
