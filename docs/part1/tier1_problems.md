---
parent: The Problems with Network Tiers
nav_order: 2
---

# What's Wrong With The Tier 1 Definition

There are many problems, here are just some of them...

## Abuse of Privilege

There are circa 85k networks which make up the Internet at the time of writing.

```text
curl -s "https://stat.ripe.net/data/ris-asns/data.json" | jq .data.counts
{
"total": 85859
}
```

They all need to buy IP Transit to reach the reset of the networks on the Internet, except for the [less-than-20 networks](tier1_asns.md) which make up the Tier 1 "[club](https://en.wikipedia.org/wiki/Old_boy_network)". The fact that this number is so small should raise alarm bells because such exclusivity implicitly creates a position of privilege, and privilege creates the potential for abuse. The abuse of privilege materialises in the form of double standards when it comes to establishing settlement free peering. Tier 1s will not peer for free with any network outside of the Tier 1 club. If they did, other networks could attain Tier 1 status simply by peering with all the Tier 1 networks.

It could be argued that the Tier 1 networks are simply the biggest networks, they worked hard to get to where they are, and they have the right not to peer with any other networks for free. The problem with this argument, is that all Tier 1s have peerings with all other Tier 1s, and due to the unending demand for data, they are constantly upgrading these peerings. This means the Tier 1s are actively investing in their free peerings, but (in my opinion) in a way which only serves to maintain their own privileged status (in a way which maintains their Tier 1 status by maintaining their peerings with all other Tier 1s). But because they don't engage with free peerings with non Tier 1 networks, performance issues occur, and it's the end users which suffer.

The reluctance from Tier 1 networks to peer with anyone who is not a Tier 1, for free, is expertly demonstrated by [AS3320 - Deutsche Telekom AG](https://www.peeringdb.com/asn/3320) (a.k.a. "DTAG").

[Meta](https://www.peeringdb.com/net/979) operates a content distribution network with users all over the world. It is normal to buy upstream connectivity (called "IP Transit") so that Meta's global user base can access Meta's content. It is also normal for Meta to establish SFIs with networks they exchange large amounts of data with. It's in the interest of both parties to exchange the traffic directly, for free, rather than both parties paying an IP Transit provider to transport the traffic between their networks (double paying).

In the case of DTAG, it is in Meta's interest to peer directly with DTAG, to avoid paying Meta's upstream Tier 1 providers to exchange traffic with end users behind the DTAG network. In this specific case, DTAG wouldn't be paying for the existing connectivity to Meta, this is because they are peering with all the other Tier 1s for free. Despite being free for DTAG to exchange traffic through a "middle man" Tier 1 between DTAG and Meta, it is still in DTAGs interest to peer directly with Meta to improve the quality and reliability of connectivity to Meta content for DTAG's customers. Meta have been exchanging several terabits per second of traffic with DTAG, which means they are an important source of traffic for DTAGs customers. This is the level of traffic a network operator would really want to have direct control over, and not rely on an intermediary (an IP Transit provider).

But this is not possible, DTAG **only** peers for free with other Tier 1s. To resolve this issue, Meta paid DTAG to get direct connectivity with DTAG. DTAG abused their Tier 1 status in two ways here:

* DTAG forced Meta to pay, simply because of their status.
* DTAG charges non-Tier 1 networks some of the highest prices **in the world** for this connectivity (way more than Meta would pay to send the traffic via an intermediary Tier 1).

Meta eventually [decided to stop paying](https://www.datacenterdynamics.com/en/news/deutsche-telekom-slams-meta-as-direct-peering-agreement-ends/) DTAGs extortionate price and it didn't end well for either party (Meta had to make a huge back payment to DTAG and traffic between the two now goes via an intermediary Tier 1 using a special peering agreement).

This is not an isolated incident, just a well known one. Cogent [tried to sue DTAG](https://cogentco.com/files/docs/news/press_releases/Cogent_Sues_Deutsche_Telekom_for_Congesting_Internet_Connections.pdf) in 2015 due to DTAG not upgrading their peering connections and allowing the links to congest.

At the time of writing, Arelion (AS1299) have congestion on one of their peerings with DTAG during peak hours in the evenings (no public link here, I opened a support case with Arelion and they confirmed it in the case).

There is now an ongoing legal dispute in the EU led by [Netzbremse](https://netzbremse.de/en/) about how DTAG requires networks to pay to interconnect with DTAG and how that causes performance problems, which impacts the end users ([recent talk at DENOG17](https://www.youtube.com/watch?v=AAXwZ23YwEY)).

Various networks around the world (including non Tier1 networks) charge other networks for the "privilege" of peering with them (sometimes because of their Tier 1 status, sometimes because they are a monopoly operator in a given geographic market e.g., KT, Telefonica, China Telecom, etc.). As a result, traffic is routed in weird and wonderful ways to avoid paying, and it's the end users that suffer. The important observation for this section, is that Tier 1 networks have been known to prioritise protecting their status over the quality and reliability of connectivity, and (ab)use their status to charge high prices.

## The Exclusivity of Being A Tier 1 Is A Curse

Tier 1 status is implicitly exclusive due it's rarity. It is widely viewed within the network operator community as prestigious to be a Tier 1 network, and keeping the status exclusive, is what maintains prestigiousness. It is a zero sum game because the more networks which have Tier 1 status, the less exclusive it is, and thus the less prestigious. This means that all Tier 1s are not only incentivised to _not_ let other networks join the club, they are also under pressure to _remain_ in the club.

Tier 1s can't pay for connectivity. As soon as they pay another network for connectivity to a specific corner of the Internet, they no longer meet the definition of being able to reach the entire Internet via directly connected customers and SFIs. They also can't peer for free with another network, because this risks letting other networks join the club and break the exclusivity. These constraints lead to connectivity problems that non-Tier 1 networks don't face:

* Sometimes poor connectivity exists between Tier 1s because neither party is willing to pay the other for the connectivity between them, in order to achieve a satisfactory level of connectivity quality. But they have to keep their SFIs barely alive to maintain their membership in the Tier 1 club. They are hoisted by their own petard.

* If the SFI agreement between Tier 1s comes with a requirement to maintain a certain traffic ratio, and one party is nearing the limit of the traffic ratio, and the link is becoming congested; then adding more capacity would enable that same one party to go out of the agreed ratio and require them to start paying the other party for the connectivity. Therefore, maintaining the congestion is in their financial interest. Also, if they pay for going out of ratio, they are no longer meeting the Tier 1 criteria of not paying for connectivity (and because unexpected traffic phenomena occur for time to time, this does happen for short periods!).

* There may be no contract when establishing an SFI, and if there is no contract neither side is obligated to do anything when SFIs become congested or to establish SFI in new locations when needed (even if there is a peering contact, if no money is exchanged the contract often has no "weight"). If legally binding paid connectivity was in place, both parties would have the ability to raise a support ticket with an SLA, escalate if the issue doesn't get resolved, and take their business elsewhere as a last resort. This is an advantage Tier 2s have over Tier 1s. Tier 1s aren't able to do this because they'd exit the club and forfeit their Tier 1 status.

* A Tier 2 or Tier 3 network has the option to re-route traffic between different upstreams to route around fibre cuts or congested links. If more capacity is needed a Tier 2 or Tier 3 network can pay extra to get the provider to increase their capacity, or buy from a different provider who has more capacity, or more resiliency, or lower latency, or whatever is not currently being provided. Tier 1s can't do this. They are in a deadlock. Some Tier 1 operators have told me, when their Tier 1 peers are congested, the peer may try to shove traffic other to other Tier 1 in a way they shouldn't be doing, but they can't exactly de-peer them. Or can they...

* Peering disputes have been happening for decades (and yes, Cogent are regularly involved!). When this happens, it is the customers who suffer because certain destinations are unreachable, traffic takes a very scenic route resulting in massive latency increases, or congested paths are used resulting is massive packet loss. Below are just a few examples, there have been many, many, disputes over the years, and they continue to this day:
  * [Cogent <> TATA](https://seclists.org/nanog/2024/May/115), [Cogent <> NTT](https://www.thinkbroadband.com/news/9896-ntt-cogent-peering-dispute-increasing-latency-for-some-routes), [Cogent <> Verizon](https://www.telecomramblings.com/2013/06/verizon-cogent-tussle-over-peering-and-netflix/), [Cogent <> Sprint](https://www.datacenterknowledge.com/business/sprint-cogent-resume-peering-keep-arguing), [Cogent <> Limelight](https://www.datacenterknowledge.com/networking/cogent-de-peers-limelight-networks), [Cogent <> ATT](https://mailman.nanog.org/pipermail/nanog/2025-January/227184.html), [Cogent <> Telia](https://www.wired.com/2008/03/isp-quarrel-par/).
    * I have had several people who are customers of Tier 1's show me bona fide evidence which is not publicly referenceable of additional peering disputes, these are a few examples:
      * TI Sparkle restricting traffic to Orange/FT and DTAG - 2025-01
      * Arelion and NTT not peering inside Europe - 2025-01
      * Arelion and Orange/FT having congested peerings - 2025-02
  * Due to the rise of massive content networks with extensive peering, Tier 1s don't carry the bulk of Internet traffic. More and more peering disputes are now happening between Tier 1s/large Tier 2s and the hyperscalers, instead of between Tier 1s. These disputes are easy to find using your favourite search engine.
  * To this day, [the most famous peering dispute of all time](HE_cake.jpeg), Cogent and HE de-peering IPv6 traffic, is still ongoing. HE customers _still_ can't reach IPv6 prefixes belonging to Cogent (this started in 2009!). Just search for any [Cogent IPv6 prefix](https://bgp.he.net/AS174#_prefixes6) using the [HE Looking Glass](https://lg.he.net/), or look on the HE route server and observe there are no routes via AS174:
    ```text
    route-server> show ipv6 bgp regexp _174_ 
    route-server>
    ```
    This also throws into question if HE and Cogent are actually Tier 1s for IPv6 traffic, if they don't have full table v6 connectivity? HE also aren't transit free for v4, so _how_ can they be a Tier 1?!

This is very anecdotal and hard to provide irrefutable data for, because this mainly comes from private chats, having bought connectivity from these networks, having spoken with them at conferences, having read through their contracts, and so on:

* Some Tier 1 networks have restrictions on how much traffic customers can exchange with the other Tier 1 networks they have SFIs with.
* Some Tier 1 networks knowingly allow their SFI with other Tier 1s to congest.
* Some Tier 1 networks only peer with other Tier 1s outside countries of interest. Peering inside countries of interest costs money.
* Some Tier 1 networks create regional peerings with other Tier 1 networks, but not in all regions i.e., they have a peering in APAC but it's for APAC traffic only, and in LATAM they don't peer.

## The Current Tier 1s Didn't Earn Their Status

Some of the Tier 1 networks (Orange/France Telecom, DTAG, TI Spark/Seabone) have their roots in the former state owned national telecommunications company of their respective origin countries (there have been many M&As along the way of course). The foundations of these networks were built with tax payers money, but today they no longer seem to want to serve for the good of the people.

Despite having various similarities with say DTAG, why aren't BT or Telstra Tier 1 networks (for clarity, I don't think they should be!)? India and China are both larger than the UK, France, Germany, and Italy; why aren't Bharti Airtel and China Telecom Tier 1s but Orange and TI Sparkle are?

This inherited status of having been around early enough, and large enough (at the time) to establish SFI with the other Tier 1s, is seemingly mistaken for hard data showing how the status was fairly earned. Interestingly, [earlier accounts](https://archive.nanog.org/meetings/nanog45/presentations/Tuesday/Brown_Internet_Peering_N45.pdf) of which networks are the Tier 1s, contain a different set of networks to the generally accepted list of today.

## Hot Potato Routing

The Internet is massively reliant on PNIs and embedded caches, in terms of peak traffic load (and to a lesser extent, IXPs). The bulk of traffic is not carrier via IP Transit. Tier 1 networks may peer with a non Tier 1 network (albeit only a select handful) for free, on the proviso that the Tier 1 only provides reachability to its on-net customer prefixes and if the peer wants transit connectivity, they need to pay for it. But they are fairly well incentivised to not peer other networks.

As already mentioned, if another network could peer with all Tier 1s, that network implicitly becomes a new Tier 1, devaluing this status based purely on exclusivity, as more an more networks achieve it. In addition, for networks which sell IP Transit as a service, it is in their best interest to peer with as few other networks as possible, because every peer is a potential customer they can no longer have. This creates a chicken and egg problem though; nobody wants to buy connectivity from a network which isn't well peered. However, the more a network peers, the smaller the pool of potential customers becomes. And it's not just about the number of networks, but the type too; access networks want connectivity to content networks and vice versa. Somehow a network selling IP connectivity needs to develop a large amount of customers with as few peers as possible, in order to achieve maximal revenues. Simply having Tier 1 status breaks this chicken and egg cycle; other network operators want to buy from Tier 1s de facto, regardless of whether that Tier 1 actually has the best connectivity for the requirement, and peering with a Tier 1 is (usually) not an option, so paying is the only way forward.

If a company wants to make it their business to sell IP connectivity, and thus avoid free peering, that is their choice. However, many Tier 1s operate global networks with high international connectivity costs, and due to the never ending pressure to reduce the price per bit, they are forced to operate a [hot potato routing](https://en.wikipedia.org/wiki/Hot-potato_routing) model. The result is that the customer pays for transit connectivity which doesn't guarantee good quality connectivity, because the Tier 1 isn't densely peering in the destination market. Compare this to a Tier 2 with an open peering policy; many Tier 2s have much richer and denser peering in their home markets than any Tier 1 could achieve when coming in from the outside. As a result, Tier 2s can operate cold potato routing within their home market and provide superior connectivity.

One notable exception to this is Hurricane Electric (AS6939), they seem to want to peer with anyone and everyone. It is hard to understand how they gain customers, but they do have an [extremely well peered network](https://bgp.tools/rankings/all?sort=peering) as a result of their open peering policy.
