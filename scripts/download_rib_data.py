#!/usr/bin/env python3

import argparse
import multiprocessing
import os
import random
from typing import Optional

import requests
from inc.data_sources import Collectors
from inc.globals import BGP_RIBS_PATH

cli_args: argparse.Namespace


def download_file(args: tuple[str, str]) -> Optional[str]:
    """
    Download an MRT file from the given url,
    and save it as the given filename.
    """

    filename, url = args
    if not url:
        raise ValueError("Missing URL")
    if not filename:
        raise ValueError("Missing output filename")

    os.makedirs(os.path.dirname(filename), exist_ok=True)

    if os.path.exists(filename):
        print(f"{os.getpid()}: Not overwriting existing file {filename}")
        return None

    print(f"{os.getpid()}: Downloading {url} to {filename}")

    headers = {
        "User-Agent": "BGP Research - Slack contact jwbensley@netldn.slack.com"
    }

    try:
        """
        The default Accept-Encoding is gzip, which causes the server
        to respond with a Content-Length which is not the full file
        size. Replace this so we can later compare the file size:
        """
        headers["Accept-Encoding"] = "*"
        resp = requests.get(url, headers=headers, stream=True)
    except requests.exceptions.ConnectionError as e:
        print(f"{os.getpid()}: Couldn't connect to HTTP server: {e}")
        return None
    except requests.exceptions.MissingSchema as e:
        print(f"{os.getpid()}: Invlaid URL, schema is missing: {e}")
        return None

    if resp.status_code != 200:
        if resp.status_code == 404:
            print(f"{os.getpid()}: ERROR: Unable to download file, 404: {url}")
            return None
        print(f"{os.getpid()}: HTTP error: {resp.status_code}")
        print(f"{os.getpid()}: {resp.url}")
        print(f"{os.getpid()}: {resp.text}")
        print(f"{os.getpid()}: {resp.content.decode()}")
        return None

    local_size = 0
    file_len = int(resp.headers["Content-length"])

    if file_len == 0:
        print(f"{os.getpid()}: File lenth is zero!")
        print(f"{os.getpid()}: {resp.url}")
        print(f"{os.getpid()}: {resp.text}")
        print(f"{os.getpid()}: {resp.content.decode()}")
        return None

    # Don't download if the file size has not changed
    if local_size == file_len:
        print(f"{os.getpid()}: Not downloading, unchanged file size for {url}")
        return url

    rcvd = 0
    print(f"{os.getpid()}: File size is {file_len/1024/1024:.7}MBs")
    progress = 0.0

    with open(filename, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024):
            if resp.status_code != 200:
                print(f"{os.getpid()}: HTTP error: {resp.status_code}")
                print(f"{os.getpid()}: {resp.url}")
                print(f"{os.getpid()}: {resp.text}")
                print(f"{os.getpid()}: {resp.content.decode()}")
                f.close()
                os.unlink(filename)
                return None

            rcvd += len(chunk)
            f.write(chunk)
            f.flush()

            if rcvd == file_len:
                print(
                    f"{os.getpid()}: Downloaded {rcvd}/{file_len} "
                    f"({(rcvd/file_len)*100}%)"
                )
            elif ((rcvd / file_len) * 100) // 10 > progress:
                # print(
                #     f"{os.getpid()}: Downloaded {rcvd}/{file_len} ({(rcvd/file_len)*100:.3}%)"
                # )
                progress = ((rcvd / file_len) * 100) // 10

    return url


def download_files(downloads: list[tuple[str, str]]) -> None:
    pool = multiprocessing.Pool(cli_args.p)
    downloaded_urls = pool.map(download_file, downloads)
    pool.close()
    print(f"Downloaded {len([x for x in downloaded_urls if x])} URLs")


def get_download_urls() -> list[tuple[str, str]]:
    downloads: list[tuple[str, str]] = []

    archives: set[str] = set()

    for collector in Collectors.Collector:

        if (
            (cli_args.npch and collector.is_pch())
            or (cli_args.nris and collector.is_ris())
            or (cli_args.nrv and collector.is_rv())
        ):
            continue

        archives.add(collector.archive())

        for url in collector.get_collector_urls(cli_args.timestamp):
            filename = os.path.basename(url)

            if collector.is_pch():
                # All PCH filenames start with "route-collector"
                file_path = os.path.join(cli_args.output, filename)

            else:
                if collector.is_rv():
                    """
                    Ensure all RouteViews files start with the same prefix.
                    Some of the files has hosted on the HTTP server are missing
                    this prefix.
                    """
                    if not collector.startswith("route-views"):
                        collector = "route-views." + collector

                file_path = os.path.join(
                    cli_args.output, f"{collector}.{filename}"
                )
            downloads.append((file_path, url))

    print(
        f"Generated {len(downloads)} URLs for {len(archives)} archive(s): "
        f"{archives}"
    )
    return downloads


def parse_cli_args() -> None:
    parser = argparse.ArgumentParser(
        description="Download RIB dump files from various public sources, "
        "only for the given timestamp",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-npch",
        help="Don't download PCH RIB files",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-nris",
        help="Don't download RIPE RIS RIB files",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-nrv",
        help="Don't download RouteViews RIB files",
        default=False,
        action="store_true",
        required=False,
    )
    parser.add_argument(
        "-output",
        help="Path to output directory for downloaded RIB files",
        type=str,
        metavar="path",
        default=BGP_RIBS_PATH,
    )
    parser.add_argument(
        "-p",
        help="No. of processes to start",
        type=int,
        default=multiprocessing.cpu_count() - 1,
    )
    parser.add_argument(
        "timestamp",
        help="yyyymmdd.hhmm timestamp of RIB dump to download. "
        "E.g. 20250701.0000",
        type=str,
    )
    global cli_args
    cli_args = parser.parse_args()


def randomise_urls(downloads: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    Randomise the list to download from different sources in parallel
    """

    randomised: list[tuple[str, str]] = []

    while len(downloads):
        i = random.randint(0, len(downloads) - 1)
        randomised.append(downloads.pop(i))
    return randomised


def main() -> None:
    parse_cli_args()
    downloads = randomise_urls(get_download_urls())
    download_files(downloads)


if __name__ == "__main__":
    main()
