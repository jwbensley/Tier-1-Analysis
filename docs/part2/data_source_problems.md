# Data Source Problems

## Public Sources of Statistics

There are various publicly available sources for data on the [DFZ](https://en.wikipedia.org/wiki/Default-free_zone) and networks inside the DFZ. The problem is that everyone has a different view of the DFZ, there is no one single DFZ and thus everyone has a slightly different idea about the topology of rest of the Internet.

Lets take an example well connected network, AS13335 (Cloudflare), and look at different public providers of connectivity stats. At the time of writing:

[bgp.he.net](https://bgp.he.net/AS13335) shows the following:

```text
BGP Peers Observed (all): 1,597
BGP Peers Observed (v4): 1,527
BGP Peers Observed (v6): 744
```

[bgp.tools](https://bgp.tools/as/13335#connectivity) shows the following:

```text
Peers Upstreams Downstreams  
2237  290       748 (Cone: 749)  
```

[asrank.caida.org](https://asrank.caida.org/asns?asn=AS13335&type=search) shows the following:

```text
customer cone
    728 asn
    15255 prefix
    18762102 address
AS degree
    1361 global
    1043 transit
    282 provider
    352 peer
    727 customer
```

As we can see, there are some similarities but also some discrepancies. So it's tricky to use data from these sources to extract the information needed.

## Public MRT Sources

Another option is to download the MRT files from route collectors, which have BGP sessions with networks of interest. This brings a different problem, the majority of networks in the world _do not_ peer with public route collectors like [RouteViews](https://archive.routeviews.org/peers/peering-status.html) and [RIS](https://www.ris.ripe.net/peerlist/all.shtml), or private collectors like [bgp.tools](https://bgp.tools/credits).

Using [BGP Kit](https://ui.broker.bgpkit.com/) one can match ASNs to route collectors:

The following table shows the list of the ASNs of interest, and which route collector has a full table feed from each ASN (some ASNs might provide a full table feed to multiple collectors, but only one is listed):

| ASN    | Name                                   | Tier | Collected          | Collector | Notes |
|--------|----------------------------------------|------|--------------------|-----------|-------|
| 174    | Cogent                                 | 1    | :white_check_mark: | RRC25     |       |
| 701    | Verizon/UUNET                          | 1    | :x:                | None      | route-views6 receives only v6 routes, no v4. |
| 1273   | Vodafone                               | 2    | :x:                | None      | RRC03 receives v6 only. |
| 1299   | Arelion                                | 1    | :white_check_mark: | RRC01     |       |
| 2635   | Automattic                             | 2    | :x:                | None      | Not peering with RIS or RV. |
| 2914   | NTT                                    | 1    | :white_check_mark: | RRC01     |       |
| 3257   | GTT                                    | 1    | :white_check_mark: | RRC01     |       |
| 3320   | DTAG                                   | 1    | :white_check_mark: | RRC01     |       |
| 3356   | Lumen/Colt                             | 1    | :x:                | None      | Not peering with RIS. route-views receives v4 only, no v6, but and doesn't export to MRT. |
| 3491   | PCCW/Console Connect                   | 1    | :white_check_mark: | RRC01     |       |
| 4637   | Telstra                                | 2    | :x:                | None      | RIS receives partial table only. Same on Route Views. |
| 5511   | FT/Orange                              | 1    | :x:                | None      | RIS receives partial table only. Same on Route Views. |
| 6453   | TATA                                   | 1    | :white_check_mark: | RRC03     |       |
| 6461   | Zayo                                   | 1    | :white_check_mark: | RRC01     |       |
| 6762   | TI Sparkle/Seabone                     | 1    | :white_check_mark: | RRC12     |       |
| 6830   | Liberty Global                         | 1    | :white_check_mark: | RRC01     |       |
| 6939   | Hurricane Electric                     | 1*   | :white_check_mark: | RRC01     |       |
| 7018   | AT&T                                   | 1    | :white_check_mark: | RRC00     |       |
| 7195   | EdgeUno                                | 2    | :x:                | None      | RIS receives partial table only. Same on Route Views. |
| 7473   | Singapore Telecommunications           | 2    | :x:                | None      | Not peering with RIS or RV. |
| 9002   | RETN                                   | 2    | :white_check_mark: | RRC01     |       |
| 9498   | Bharti Airtel                          | 2    | :x:                | None      | Not peering with RIS or RV. |
| 12389  | Rostelecom                             | 2    | :x:                | None      | Not peering with RIS or RV. |
| 12956  | Telxius/Telefonica                     | 1    | :white_check_mark: | RRC03     |       |
| 13335  | Cloudflare                             | 2    | :x:                | None      | RIS receives partial table only. Same on Route Views. |
| 13786  | Seaborn (Seabras USA)                  | 2    | :white_check_mark: | RRC15     |       |
| 14840  | BR.DIGITAL                             | 2    | :white_check_mark: | RRC25     |       |
| 20473  | The Constant Company / Vultr           | 2    | :x:                | None      | RIS receives partial table only. Same on Route Views. |
| 23911  | China Next Generation Internet Beijing | 2    | :x:                | None      | Not peering with RIS or RV. |
| 24482  | SG.GS                                  | 2    | :white_check_mark: | RRC00     |       |
| 35280  | F5 Networks                            | 2    | :white_check_mark: | RRC15     |       |
| 36236  | NetActuate                             | 2    | :white_check_mark: | RRC25     |       |
| 37468  | Angola Cables                          | 2    | :white_check_mark: | napafrica |       |
| 37721  | Virtual Technologies & Solutions       | 2    | :x:                | None      | RRC00 receives full v6 table but 857k v4 routes. |
| 38255  | China Education and Research Network   | 2    | :x:                | None      | Not peering with RIS or RV. |
| 39120  | Convergenze                            | 2    | :white_check_mark: | amsix     |       |
| 49544  | i3D.net                                | 2    | :white_check_mark: | RRC00     |       |
| 52320  | GlobeNet Cabos Submarinos Colombia     | 2    | :white_check_mark: | RRC16     |       |
| 57463  | NetIX Communications                   | 2    | :x:                | None      | route-views2 has partial v4 table and no v6. route-views6 has no v4 but full table v6. RRC10 partial table only. |
| 64289  | Macarne                                | 2    | :white_check_mark: | sfmix     |       |
| 199524 | G-Core                                 | 2    | :white_check_mark: | RRC03     |       |

The table shows that all the data needed can't be pulled from direct peerings with public route collectors.

## Proxy ASNs

For some of the ASNs of interest there is no data available via public MRT archives (some of the ASNs do not peer with any RouteViews or RIPE collectors, or they peer with the collectors which don't export MRTs, or even if they do peer they don't send their full BGP table to the collectors). In this case it might be possible to get the data for those ASNs another way.

By finding another ASN (the term "proxy ASN" is used here) which does send a full BGP table to a public BGP collector, where the proxy ASN is a downstream of the ASN of interest, and that proxy ASN has no other upstream (in other words, it's single homed to the ASN of interest); the full table export from the proxy ASN is essentially a full table export of the ASN of interest.

The following is the list of ASNs of interest for which there is no MRT full table data available:

| ASN   | Name                                   |
|-------|----------------------------------------|
| 701   | Verizon/UUNET                          |
| 1273  | Vodafone                               |
| 2635  | Automattic                             |
| 3356  | Lumen/Colt                             |
| 4637  | Telstra                                |
| 5511  | FT/Orange                              |
| 7195  | EdgeUno                                |
| 7473  | Singapore Telecommunications           |
| 9498  | Bharti Airtel                          |
| 12389 | Rostelecom                             |
| 13335 | Cloudflare                             |
| 20473 | The Constant Company / Vultr           |
| 23911 | China Next Generation Internet Beijing |
| 37721 | Virtual Technologies & Solutions       |
| 38255 | China Education and Research Network   |
| 57463 | NetIX Communications                   |

### Finding Proxy ASNs via Caida

Caida has data which can be used to find suitable proxy ASNs.

```bash
mkdir -p raw_data/downstreams

asns="701 1273 2635 3356 4637 5511 7195 7473 9498 12389 13335 20473 23911 37721 38255 57463"
```

Get a list of AS relations between all ASNs in the DFZ:

```bash
# You must sign the following form if you plan to publish any research based on Caida's data:
# https://www.caida.org/catalog/datasets/request_user_info_forms/as_relationships/
wget -O raw_data/downstreams/20241101.as-rel2.txt.bz2 https://publicdata.caida.org/datasets/as-relationships/serial-2/20241101.as-rel2.txt.bz2
bunzip2 raw_data/downstreams/20241101.as-rel2.txt.bz2
```

For each ASN of interest, find all the downstreams which are singled homed to that ASN of interest:

```bash
for asn in $asns
do
    ./find_single_homed_asns.py raw_data/downstreams/20241101.as-rel2.txt $asn
done
```

Get a list of peers for all RouteViews and RIS collectors:

```bash
# Parse through jq to have nice output formatting
curl https://api.bgpkit.com/v3/broker/peers | jq > raw_data/downstreams/bgpkit.peers.json
```

For each single homed ASN, check if it is exporting a full table feed to a collector:

```bash
for asn in $asns
do
    echo "Checking single homed downstreams of $asn"
    jq -c '.[]' "raw_data/downstreams/${asn}_sh_downstreams.json" | while read downstream_asn
    do
        ./scripts/find_collector_mrt_for_asn.py raw_data/bgpkit.peers.json "$downstream_asn"
    done | jq ".|select(.[]!={})"
    echo ""
done
```

After looking through the results and choosing proxy ASNs which are exporting a full table to one of the public MRT sources, the table now looks like this:

| ASN   | Name                                   | Proxy ASN          | Proxy Collector |
|-------|----------------------------------------|--------------------|-----------------|
| 701   | Verizon/UUNET                          | 54316              | RRC25           |
| 1273  | Vodafone                               | 12969              | RRC01           |
| 2635  | Automattic                             | :x:                | None            |
| 3356  | Lumen/Colt                             | 13830              | RRC00           |
| 4637  | Telstra                                | :x:                | None            |
| 5511  | FT/Orange                              | :x:                | None            |
| 7195  | EdgeUno                                | 64116              | RRC24           |
| 7473  | Singapore Telecommunications           | :x:                | None            |
| 9498  | Bharti Airtel                          | :x:                | None            |
| 13335 | Cloudflare                             | :x:                | None            |
| 12389 | Rostelecom                             | :x:                | None            |
| 20473 | The Constant Company / Vultr           | :x:                | None            |
| 23911 | China Next Generation Internet Beijing | :x:                | None            |
| 37721 | Virtual Technologies & Solutions       | :x:                | None            |
| 38255 | China Education and Research Network   | :x:                | None            |
| 57463 | NetIX Communications                   | :x:                | None            |

### Proxy ASN Problems

It's hard to know the relationship between two ASNs. There are problems with the Caida data used to get ASN relationship. For example, it states that AS9002 (RENT) is single homed behind 3356 (Lumen) which is incorrect. At the time of writing AS1299 (Arelion) and AS3257 (GTT) are both providing transit to AS9002 (checked from a router CLI with full table feeds from 1299 and 3257). There are lots of mistakes like this.

The proxy ASN method still leaves a lot of data missing and it's not clear it would work when considering the errors in the Caida data. Therefore, the proxy ASN method isn't suitable to "fill in the blanks".

## PCH Collectors

In addition to the RouteViews and RIS collectors which provide [Public MRT dumps](#public-mrt-sources), PCH also operate a large number of collectors, which provide [BGP table dumps](https://www.pch.net/resources/Routing_Data/) in a rather horrible, unstructured output, that isn't even consistent across collectors!

But again, PCH alone doesn't have feeds from all the [networks of interest](../part1/asns_of_interest.md#final-asn-list).
