#!/bin/bash

set -e

function print_help {
    echo ""
    echo "You must choose exactly ony of the following options"
    echo ""
    echo "-c    Copy files to remove server"
    echo "-i    Install python and dependencies on remote server"
    echo ""
    echo "$0 -i 10.0.0.1 user123"
    echo "$0 -c 10.0.0.1 user123"
    echo ""
}

if [[ $# -ne 3 ]]
then
    print_help
    exit 1
fi

set -eu

SERVER="$2"
USER="$3"
BASE="/mnt/data/tier1_stats/"

if [ "$1" == "-c" ]
then
    echo "Copying files to server..."
    ssh ${USER}@${SERVER} "mkdir -p ${BASE} && mkdir -p ${BASE}/scripts && mkdir -p ${BASE}/scripts/inc"
    scp requirements_py310.txt ${USER}@${SERVER}:${BASE}
    scp requirements_py311.txt ${USER}@${SERVER}:${BASE}
    scp run.sh ${USER}@${SERVER}:${BASE}
    scp scripts/*.py ${USER}@${SERVER}:${BASE}/scripts/
    scp scripts/inc/*.py ${USER}@${SERVER}:${BASE}/scripts/inc/
    echo "Done"
elif [ "$1" == "-i" ]
then
    echo "Installing dependencies on server..."
    ssh ${USER}@${SERVER} "
    sudo apt-get install --no-install-recommends -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    build-essential \
    libssl-dev \
    libffi-dev

    cd ${BASE}/
    python3.11 -m venv --without-pip .venv
    source .venv/bin/activate
    python3.11 -m ensurepip
    python3.11 -m pip install -r requirements_py311.txt
    "
    echo "Done"
fi
