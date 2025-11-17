import os

import orjson
import requests
from requests import Response

request_headers = {
    "User-Agent": "BGP Research - Slack contact jwbensley@netldn.slack.com"
}


def get_url(url: str) -> Response:
    """
    Get data from $url and return the response.
    """

    print(f"Downloading: {url}")
    resp = requests.get(url, headers=request_headers)
    if resp.status_code != 200:
        print(f"HTTP error: {resp.status_code}")
        print(resp.url)
        print(resp.text)
        print(resp.content)
        resp.raise_for_status()

    return resp


def get_url_to_file(filename: str, url: str, overwrite: bool = False) -> str:
    """
    Get data from $url and save it to $filename.
    Return the filename.
    """

    if os.path.exists(filename):
        if not overwrite:
            print(f"Not overwriting existing file {filename}")
            return filename

    resp = get_url(url)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        f.write(resp.text)
    print(f"Wrote to {filename}")

    return filename


def get_json_to_file(filename: str, url: str, overwrite: bool = False) -> str:
    """
    Get $url and save to $filename.
    Parse through json.load to nicely format output.
    Return the filename.
    """

    if os.path.exists(filename):
        if not overwrite:
            print(f"Not overwriting existing file {filename}")
            return filename

    resp = get_url(url)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        f.write(orjson.dumps(resp.json(), option=orjson.OPT_INDENT_2))
    print(f"Wrote to {filename}")

    return filename
