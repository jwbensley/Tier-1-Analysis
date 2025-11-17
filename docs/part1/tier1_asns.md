# Tier 1 ASNs

In order to do some analysis and compare Tier 1s and non Tier 1s, we're going to need to identify who is / is not a Tier 1.

## Who Are The Tier 1s?

Identifying who are the Tier 1 networks is quite tricky. There are a few reasons for this:

* [Caida](https://asrank.caida.org/about) and [bgp.tools](https://bgp.tools/) both try to infer the (commercial) relationship between networks by looking at advertisements in the global routing table. The BGP control-plane can't be used to infer the commercial relationship between a pair of networks. The required information simply isn't present. Tools like Caida and bgp.tools have to _guess_ the nature of a BGP peering (are the two networks peers, or in an upstream/downstream relationship), which means there are mistakes (don't interpret that is criticism of these tools, they are both great, the point here is, this is a tricky problem).

Here are some examples:

  * AS4134:
    * bgp.tools lists AS1299 as an upstream of AS4134: <https://bgp.tools/as/4134>.
    * Caida lists AS4134 as a peer of AS1299: <https://asrank.caida.org/asns/4134>.
    * AS-CN and AS4134 don't appear as members in any of AS1299's AS-SETs, suggesting they are peers: <https://irrexplorer.nlnog.net/as-set/AS-CN>, <https://irrexplorer.nlnog.net/asn/AS4134>.

  * AS1273:
    * bgp.tools lists AS1299 as an upstream of AS1273 <https://bgp.tools/as/1273>.
    * Caida lists AS1273 as a customer of AS1299.
    * AS1273:AS-CWW does appear as a member in AS1922's North American AS-SET, suggesting they are a customer: <https://irrexplorer.nlnog.net/as-set/AS1273:AS-CWW>
    * See the note below about how AS1273 has a dedicated BGP community from AS1299 under their "peer" section.

  * A5405:
    * bgp.tools lists AS12956 as an upstream of AS5405: <https://bgp.tools/as/5405>
    * Caida lists AS12956 as a peer of AS5405: <https://asrank.caida.org/asns?asn=5405>
    * AS5405:AS-INTERDOTLINK / AS5405 don't appear in Telxius' AS-SET, suggesting they are peers: <https://irrexplorer.nlnog.net/as-set/AS-TDATANET>.
    * As an employee of AS5405 I can confirm AS5405 is a peer of Telxius, not an IP Transit customer.

* The relationship between networks can vary based on location. NetworkA might be a customer of NetworkB in one geography, but in a different geography they are peers.

* Even if we had access to the invoices exchanged between networks, it still wouldn't be clear who's paying who, and for what. Just because there is no line item on the monthly invoice for IP connectivity, or even if there is but it is zero rated, doesn't mean the IP connectivity isn't being paid for. If party A buys wavelengths from party B, part of the negotiation might include throwing in IP connectivity (meaning the connectivity _is_ paid for, but by the wavelength revenue).

* Today a network may claim they have no upstreams, or they may not, but still insist they are a Tier 1. There is currently no way for an external party to know the relationship between two networks (who is the provider and who is the customer). This is set to change though; as the industry starts to deploy [ASPAs](https://datatracker.ietf.org/doc/html/draft-ietf-sidrops-aspa-verification) networks will be forced to reveal their relationships between other. Then we'll see who really is upstream free (spoiler: it will be fewer than today's [generally accepted list of Tier 1s](#list-of-tier-1-networks)!).

* Some Tier 1s seem to have non-Tier 1 peers. This can be seen if you look through the BGP communities for different Tier 1s. Just one example: Arelion have do-not-announce and prepend [BGP communities](https://www.arelion.com/our-network/bgp-routing/bgp-communities) for their "peers" however, the list includes not only the usual suspects you'd find on a list of Tier 1 networks, but also: China Telecom (AS4134), China Unicom (AS4837), Comcast (AS7922), Vodafone (AS1273). Other Tier 1s have "interesting" BGP communities too. Does this mean that some of these networks are transit free, which would technically bring them into the Tier 1 club? Vodafone have told me that they (AS1273) _are_ a Tier 1. If you say so mate!

## List of Tier 1 Networks

The following table shows the generally accepted list of Tier 1 ASNs:

| ASN       | Name                 |
|-----------|----------------------|
| 174       | Cogent               |
| 701       | Verizon/UUNET        |
| ~~1239~~  | ~~T-Mobile/Sprint~~  |
| 1299      | Arelion              |
| 2914      | NTT                  |
| 3257      | GTT                  |
| 3320      | DTAG                 |
| 3356      | Lumen/Colt           |
| 3491      | PCCW/Console Connect |
| 5511      | FT/Orange            |
| 6453      | TATA                 |
| 6461      | Zayo                 |
| 6762      | TI Sparkle/Seabone   |
| 6830      | Liberty Global       |
| 6939      | Hurricane Electric   |
| 7018      | AT&T                 |
| 12956     | Telxius/Telefonica   |

There are however, various comments that can be made about this list:

* AS1239 (Sprint) are included in some lists found on the Internet, however they are no longer a Tier 1 because they were bought by AS174 (Cogent) and merged into Cogent. The network now has AS174 as it's sole upstream and is slowly being borged into AS174.
* AS1273 (Vodafone) are not in the list above, they are generally not listed in lists of Tier 1 networks found on the Internet, however, they have told me in person they are a Tier 1 (apparently!). If you agree that AS6830 is a Tier 1, then why would AS1273 _not_ also be a Tier 1?
* AS6939 (Hurricane Electric) are generally accepted as a Tier 1 for IPv6 connectivity, operating a transit free network for IPv6, but they are not transit free for IPv4.
* Due to the Cogent <> HE IPv6 peering dispute, are either of them really an IPv6 tier 1 provider? They don't have the full table for IPv6 due to their peering dispute. If you agree with this view, then HE isn't a Tier 1 at all because they don't have an IPv6 full table and buy IPv4 transit.
* Anecdotally, regarding the following ASNs, are they just really massive access networks, they don't operate extensive global backbones that are on the same scale as say 3356 or 1299. They also aren't competing to provide global connectivity to networks all over the world in the same way that Cogent/Areion/NTT/GTT/Lumen/PCCW/TATA/Zayo/HE are:
  * 701 Verizon
  * 3320 DTAG
  * 5511 Orange
  * 6762 TI Sparkle
  * 6830 Liberty Global
  * 7018 AT&T
  * 12956 Telxius

Despite these quirks, this is the list being used for the rest of this analysis (minus AS1239 / Sprint). And these quirks need to be kept in mind when looking at data relating to these ASNs.
