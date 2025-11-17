import os

U32_MAX = 2**32 - 1
U128_MAX = 2**128 - 1

IPV4_SIZE = 32
IPV6_SIZE = 128

RAW_DATA = "./raw_data"  # Base path to output raw data
BGP_RIBS_PATH = os.path.join(
    RAW_DATA, "bgp_ribs/"
)  # Where to download BGP RIB files
RIB_PATHS_PATH = os.path.join(
    RAW_DATA, "rib_paths/"
)  # Where to store the paths parsed from downloaded RIB files
MERGED_PATHS_PATH = os.path.join(
    RAW_DATA, "merged_paths/"
)  # Where to stored the merged parsed paths
ASN_GRAPHS_PATH = os.path.join(
    RAW_DATA, "asn_graphs/"
)  # Path to store rendered ASN connectivity graphs
FULL_TABLE_REPORT = os.path.join(
    MERGED_PATHS_PATH, "full_tables.json"
)  # Path to report, if a full table was reconstructed for each ASN
COVERAGE_DATA_PATH = os.path.join(
    RAW_DATA, "coverage/"
)  # Where to stored the calculated coverage stats
PLOT_PATH = os.path.join(
    RAW_DATA, "plots/"
)  # Where to store generated charts/plots

# Full table thresholds
RIS_THRESHOLDS = "ris-full-table-threshold.json"
# NRO allocated resources
NRO_ALLOCATIONS = "nro-delegated-stats"

# Output filename for calculates coverage stats
COVERAGE_AS_CONE = "as_cone_coverage.csv"
COVERAGE_AS_HOP_COUNT_ASNS = "as_hop_count_per_asn.csv"
COVERAGE_AS_HOP_COUNT_PREFIXES = "as_hop_count_per_prefix.csv"
COVERAGE_CONTINENT_BREAKDOWN = "as_continent_breakdown.csv"
COVERAGE_GLOBAL = "global-stats.json.gz"
COVERAGE_IP = "ip_coverage.csv"
COVERAGE_PEERING = "peering_coverage.csv"
COVERAGE_PEERINGS = "peerings.csv"
COVERAGE_V4 = "v4_coverage.csv"
COVERAGE_V4_SHORTER_T1 = "v4_shorter_t1.csv"
COVERAGE_V6 = "v6_coverage.csv"
COVERAGE_V6_SHORTER_T1 = "v6_shorter_t1.csv"

# Output filenames for coverage charts/plots
PLOT_AS_CONE_COVERAGE = "as_cone_coverage.html"
PLOT_AS_CONE_OVERLAP = "as_cone_overlap.html"
PLOT_AS_CONE_VISIBLE = "as_cone_visible.html"
PLOT_AS_HOPS_COUNT = "as_hops_count.html"
PLOT_AS_HOPS_WEIGHTED = "as_hops_weighted.html"
PLOT_AS_CONTINENT_BREAKDOWN = "as_continent_breakdown.html"
PLOT_FIRST_HOP_ASNS = "first_hop_asns.html"
PLOT_FIRST_HOP_UNIQUE = "first_hop_unique.html"
PLOT_FIRST_HOP_OVERLAP = "first_hop_overlap.html"
PLOT_IPV4_COVERAGE = "ipv4_coverage.html"
PLOT_IPV6_COVERAGE = "ipv6_coverage.html"
PLOT_PEERINGS = "peerings.html"
PLOT_V4_COVERAGE = "v4_coverage.html"
PLOT_V4_SHORTER_T1 = "v4_shorter_t1.html"
PLOT_V6_COVERAGE = "v6_coverage.html"
PLOT_V6_SHORTER_T1 = "v6_shorter_t1.html"
