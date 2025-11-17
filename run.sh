#!/bin/bash

function print_help {
    echo ""
    echo "You must specify a timestamp in format: yyyymmdd.hhmm"
    echo ""
    echo "$0 20250922.0000"
    echo ""
}

if [[ $# -ne 1 ]]
then
    echo "Missing CLI arg(s)"
    print_help
    exit 1
fi

set -ue

TIMESTAMP="$1"
rm -rf ./raw_data/rib_paths/ ./raw_data/bgp_ribs/ ./raw_data/merged_paths/ ./raw_data/coverage/ ./raw_data/asn_graphs/ ./raw_data/logs/

echo ""
echo "Starting at $(date)"
echo ""

source .venv/bin/activate
mkdir -p ./raw_data/logs
./scripts/download_rib_data.py "$TIMESTAMP" > ./raw_data/logs/download.log 2>&1
./scripts/parse_ribs.py ./raw_data/bgp_ribs/* > ./raw_data/logs/parse.log 2>&1
./scripts/merge_rib_stats.py ./raw_data/rib_paths/* > ./raw_data/logs/merge.log 2>&1
./scripts/count_of_merged.py -t6 190000 > ./raw_data/logs/count.log 2>&1
./scripts/coverage.py > ./raw_data/logs/coverage.log 2>&1
./scripts/plot_coverage.py
./scripts/graph_asn_connectivity.py -layout kamada -dpi 60
./scripts/graph_asn_connectivity.py -layout kamada -dpi 60 -nodesizes
./scripts/graph_asn_connectivity.py -layout kamada -dpi 150
./scripts/graph_asn_connectivity.py -layout kamada -dpi 150 -nodesizes
./scripts/graph_asn_connectivity.py -layout spring -dpi 60
./scripts/graph_asn_connectivity.py -layout spring -dpi 60 -nodesizes
./scripts/graph_asn_connectivity.py -layout spring -dpi 150
./scripts/graph_asn_connectivity.py -layout spring -dpi 150 -nodesizes
tar -cvzf "./raw_data/${TIMESTAMP}.tar.gz" ./raw_data/merged_paths/ ./raw_data/coverage/ ./raw_data/asn_graphs/

echo ""
echo "Finishing at $(date)"
echo ""
