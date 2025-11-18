---
parent: Getting and Processing the Data
nav_order: 2
---

# Getting The Data

## Reconstructing BGP Tables

Instead of using a combination of a [single public data source](data_source_problems.md#public-mrt-sources) and single [Proxy ASNs](data_source_problems.md#proxy-asns), what about scanning all ASNs from all public exporters?

For example, ASN XYZ is not peering with any public or private collectors however some XYZ downstreams are peering with public collectors. Those downstreams might be multi-homed to multiple upstreams meaning that they can't be used to get a full view of XYZ's BGP table, but they can provide the routes they prefer via XYZ (a partial table). Supposing XYZ has two downstreams, A and B, which peer with public collectors. Suppose that A and B have multiple upstreams (in addition to XYZ). A prefers 50% of the routes it receives via XYZ, and 50% via it's second upstream. B prefers 50% of the routes received from XYZ and 50% via it's second upstream. If the 50% of routes preferred via XYZ by A and B are different, then adding them together gives the full view of XYZ's BGP table.

In reality the ASNs will prefer some overlapping routes and some non-overlapping routes. But if enough BGP tables from XYZ downstreams are collected, it could be possible to reconstruct the full table for XYZ as seen by it's downstreams. Therefore, parsing the routes exported by all ASNs to all public MRTs archives gives the best chance of getting the required data.

This requires parsing all MRT files from RouteViews and RIS, and all CLI dumps from PCH, and asking the community to donate some CLI outputs to fill in the blanks.

In the case that AS65000 has two downstreams, 65001 and 65002, and 65001 sees `192.0.2.0/24` via `[ 65000 65555 ]` and 65002 sees `192.0.2.0/24` via `[ 65000 65444 65555 ]`, both paths are recorded in 65000's reconstructed table (`[ 65555 ]` and `[ 65444 65555 ]`). In the end a full table (in terms of number of prefixes) should be reconstructed for each networking being examined, and if they are available, multiple paths are stored against each prefix.

It should be noted that there are many physical connections between networks which are not seen in the data collected by public route collectors. This is because networks which contribute data to public route collectors, tend to only send their best path (the use of [Add-Path](https://www.rfc-editor.org/rfc/rfc7911.html) is rare in the DFZ).

## Parsing All Data

Let's choose a date in the past when all the MRT and CLI table dumps are available, and run the included BASH script. Note that midnight is the only timestamp that is common across all three collectors, meaning regardless of the day chosen the time must be 00:00.

```bash
./run.sh 20250922.0000
```

This script will:

* Download the MRT and CLI dumps from all collectors for the chosen date/time.
* Parse all the collector dumps and community donated CLI outputs, recording which prefixes where seen via each of the ASNs of interest, and which ASNs where reachable through one of the ASNs of interest, and if they were a direct peer (first ASN in the path) or not.
* The collected data is generated per input file (per collector) so this has to be merged into a per ASN of interest file.
* Then the total number of prefixes and ASNs seen via each ASN of interest is counted, and a table is printed showing for which ASNs we could reconstruct a full table view.
* Finally some statistics are calculated based on the reconstructed BGP tables.

Below is example output from the penultimate step above, which checks which ASNs a full table could be reconstructed for. RIPE provides a rolling definition at <https://stat.ripe.net/data/ris-full-table-threshold/data.json> of how many prefixes a network needs to have in it's BGP table to be considered as having a full table view. I think the IPv6 number is slightly too high so I've lowered it to 190K.

What is also important to note below is that these numbers are for the reconstructed table per ASN *before* any filtering happens (i.e., removing bogon prefixes and ASNs). This is to see how much data is being carried by each network, regardless of it's validity.

```bash
Prefix count per ASN:
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|    ASN |   V4 Pfxs | V4 Full Table   |   V6 Pfxs | V6 Full Table   |   ASNs | ASNs Full Table   |
+========+===========+=================+===========+=================+========+===================+
|    174 |   1006335 | True            |    209465 | True            |  80352 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|    701 |    987223 | True            |    211644 | True            |  83933 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   1273 |   1014183 | True            |    227434 | True            |  85019 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   1299 |   1019107 | True            |    229769 | True            |  85314 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   2635 |       168 | False           |        57 | False           |      1 | False             |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   2914 |   1002541 | True            |    218648 | True            |  84621 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   3257 |   1004647 | True            |    218676 | True            |  84646 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   3320 |    993823 | True            |    190953 | True            |  83909 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   3356 |   1074669 | True            |    249203 | True            |  87557 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   3491 |   1030670 | True            |    227237 | True            |  85359 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   4637 |    977419 | True            |    220760 | True            |  83324 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   5511 |   1000200 | True            |    216936 | True            |  84440 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   6453 |   1000706 | True            |    219351 | True            |  84445 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   6461 |    997786 | True            |    218829 | True            |  84423 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   6762 |   1003397 | True            |    220602 | True            |  84757 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   6830 |    993545 | True            |    218321 | True            |  84189 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   6939 |   1020897 | True            |    227109 | True            |  84796 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   7018 |    994577 | True            |    216471 | True            |  84146 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   7195 |    312462 | False           |     97843 | False           |  35733 | False             |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   7473 |    999675 | True            |    172051 | False           |  83475 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   9002 |   1006766 | True            |    223949 | True            |  84590 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|   9498 |   1024067 | True            |    205908 | True            |  84555 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  12389 |    159052 | False           |    136031 | False           |  28184 | False             |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  12956 |    996702 | True            |    218125 | True            |  84292 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  13335 |      8632 | False           |      3730 | False           |   1082 | False             |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  13786 |   1008787 | True            |    225781 | True            |  84371 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  14840 |   1011627 | True            |    225212 | True            |  84329 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  20473 |    997151 | True            |     56387 | False           |  82585 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  23911 |       395 | False           |      4403 | False           |   4247 | False             |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  24482 |   1023721 | True            |    229213 | True            |  84498 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  35280 |   1027438 | True            |    237541 | True            |  84542 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  36236 |   1033244 | True            |    244463 | True            |  84435 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  37468 |   1009234 | True            |    224757 | True            |  80309 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  37721 |    874581 | False           |    227922 | True            |  80429 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  38255 |         2 | False           |      4182 | False           |   4178 | False             |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  39120 |   1015786 | True            |    228239 | True            |  84348 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  49544 |   1033261 | True            |    234464 | True            |  84539 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  52320 |    999039 | True            |    219078 | True            |  84297 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  57463 |    535366 | False           |    223906 | True            |  68144 | False             |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
|  64289 |    998649 | True            |    220857 | True            |  84280 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
| 199524 |   1051266 | True            |    242263 | True            |  84694 | True              |
+--------+-----------+-----------------+-----------+-----------------+--------+-------------------+
```

Let's examine some of the networks which don't seem to have full v4, v6, and ASN visibility:

|    ASN |   V4 Pfxs | V4 Full Table   |   V6 Pfxs | V6 Full Table   |   ASNs | ASNs Full Table   | Result             | Comments     |
|--------|-----------|-----------------|-----------|-----------------|--------|-------------------|--------------------|--------------|
|   2635 |       168 | False           |        57 | False           |      1 | False             | :x:                | Data not found |
|   7195 |    312462 | False           |     97843 | False           |  35733 | False             | :x:                | Data not found |
|   7473 |    999675 | True            |    172051 | False           |  83475 | True              |:grey_exclamation: | V4 data pulled from a direct v4 BGP session with 7473, v6 is incomplete. A full table's worth of ASNs are also visible. 7473 will be included in v4 analysis. |
|  12389 |    159052 | False           |    136031 | False           |  28184 | False             | :x:                | Data not found |
|  13335 |      8632 | False           |      3730 | False           |   1082 | False             | :x:                | Data not found |
|  20473 |    997151 | True            |     56387 | False           |  82585 | True              | :grey_exclamation: | V4 data pulled from a direct v4 BGP session with 20473, v6 is incomplete. A full table's worth of ASNs are also visible. 20473 will be included in v4 analysis. |
|  23911 |       395 | False           |      4403 | False           |   4247 | False             | :x:                | Data not found |
|  37721 |    874581 | False           |    227922 | True            |  80429 | True              | :grey_exclamation:                | A full v6 table and full tables worth of ASN visibility has been reconstructed, but not for v4. 37721 will be included in v6 analysis. |
|  38255 |         2 | False           |      4182 | False           |   4178 | False             | :x:                | Data not found |
|  57463 |    535366 | False           |    223906 | True            |  68144 | False             | :x:                | Data not found |

The table below is the list of missing networks which will be excluded from analysis:

| ASN    | Name                                   |
|--------|----------------------------------------|
| 2635   | Automattic                             |
| 7195   | EdgeUno                                |
| 12389  | Rostelecom                             |
| 13335  | Cloudflare                             |
| 23911  | China Next Generation Internet Beijing |
| 38255  | China Education and Research Network   |
| 57463  | NetIX Communications                   |

## ASNs with Sufficient Data Availability

The table below shows the final list of ASNs for which a full table could be reconstructed:

| ASN    | Name                                   |
|--------|----------------------------------------|
| 174    | Cogent                                 |
| 701    | Verizon/UUNET                          |
| 1299   | Arelion                                |
| 2914   | NTT                                    |
| 3257   | GTT                                    |
| 3320   | DTAG                                   |
| 3356   | Lumen/Colt                             |
| 3491   | PCCW/Console Connect                   |
| 4637   | Telstra                                |
| 5511   | FT/Orange                              |
| 6453   | TATA                                   |
| 6461   | Zayo                                   |
| 6762   | TI Sparkle/Seabone                     |
| 6830   | Liberty Global                         |
| 6939   | Hurricane Electric                     |
| 7018   | AT&T                                   |
| 7473   | Singapore Telecommunications           |
| 9002   | RETN                                   |
| 9498   | Bharti Airtel                          |
| 12956  | Telxius/Telefonica                     |
| 13786  | Seaborn (Seabras USA)                  |
| 14840  | BR.DIGITAL                             |
| 20473  | The Constant Company / Vultr           |
| 24482  | SG.GS                                  |
| 35280  | F5 Networks                            |
| 36236  | NetActuate                             |
| 37468  | Angola Cables                          |
| 37721  | Virtual Technologies & Solutions       |
| 39120  | Convergenze                            |
| 49544  | i3D.net                                |
| 52320  | GlobeNet Cabos Submarinos Colombia     |
| 64289  | Macarne                                |
| 199524 | G-Core                                 |
