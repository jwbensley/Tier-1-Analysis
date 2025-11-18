---
parent: Getting and Processing the Data
nav_order: 3
---

# Processing The Data

## Caveats

> [!IMPORTANT]
> The most important point of note is that two or more BGP feeds taken from the same network can be different, and that _is_ valid.

For a given network, the routes sent to any BGP neighbour will vary based on a wide range of criteria. Two peers of the same network may receive very different routes depending on:

* Their geography
* Their political relationship
* Their commercial relationship
* How much is being paid
* The capabilities of the BGP speakers
* The security / filtering configuration in place
* Any aggregation configuration which is in place

This creates the problem that collecting multiple BGP feeds from each [ASN of interest](../part1/asns_of_interest.md), either [directly or by reconstructing it](../part2/getting_the_data.md), still provides no guarantees of the data accuracy. This is why [the overarching disclaimer](../README.md#disclaimer-about-dfz-analyses) must be recognised and understood by the reader of [the reports](../part3/).

Data from approximately 351 public route collectors has been analysed:

* RouteViews:
  * Collectors: 42
  * Full v4 tables: 297
  * Full v6 tables: 273
* RIPE RIS:
  * Collectors: 22
  * Full v4 tables: 326
  * Full v6 tables: 325
* PCH:
  * Collectors: 287
  * Full v4 tables: 1
  * Full v6 tables: 120

Despite this, it was still not possible to reconstruct even one single full table feed for AS1273. Instead I had to reach out to the community and I was provide with a full table feed from 3 different people. If a network advertises exactly the same routes to all BGP peers (which is common for small networks), three BGP feeds is plenty. If a network has high cardinality in it's routing data (which is common for large networks), three feeds might be nowhere near enough to build a reliable picture of that network.

## What Was Analysed

For each ASN of Interest ("AOI"), the BGP data was searched for prefixes where an AOI was found somewhere in the AS path. The AS path is snipped from this point onwards, where the AOI was found. We can assume that what remains is the AOI's path to the prefix. For example:

> AS65000 advertises prefix `192.0.2.0/24` with AS path `[ 65000 65001 65002 65003 ]` and we're interested in which prefixes and ASNs which AS65002 has visibility of. Then we can insert into the reconstructed table for AS65002, the prefix `192.0.2.0/24` with the AS path `[ 65002 65003 ]`.

The AS paths have also been deduplicated. The goal is to examine which networks are directly peered with each other, and which networks they have visibility of (even if not directly peered). AS prepends are an artefact of local policy and not important in terms of assessing (potential) physical connectivity. For example:

> If the following AS path is seen in the reconstructed table for AS65002: `[ 65002 65003 65003 65003 65004 ]`, then the AS path in AS65002's reconstructed table becomes `[ 65002 65003 65004 ]`.

Further to this, even though AS65002 maybe have only seen one prefix `192.0.2.0/24` with a deduped AS path of `[ 65002 65003 65004 ]`, meaning it was originated from AS65004, AS65002 must have connectivity to AS65003. So the list of directly connected ASNs for AS65002 contains AS65003, and the list of all ASNs which AS65002 has visibility of contains AS65003 and AS65004.

Any bogon prefixes and bogon ASNs are removed from the data, as well as prefixes longer then /24 for IPv4 and /48 for IPv6.
