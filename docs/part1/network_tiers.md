# What Is The Network Tiering System and What's Wrong With It?

## Overview

There is a widespread but unofficial grading system used throughout the industry to categorise the networks which collectively form _the_ [Internetwork](https://en.wikipedia.org/wiki/Internetworking).

Networks are assigned a "tier" number (either 1, 2 or, 3), and the general assumption is thus; the lower the tier number, the "better" connectivity that network has (a Tier 1 ranked network has "better" connectivity than a Tier 2 ranked network, which has better connectivity than a Tier 3 network).

## What's Wrong with Network Tiers

This tiering system is typically used to inform decisions made by customers and/or peers of a given network, when they are evaluating if they should connect with that network. For example, if the network is a lower tier, it might be worth paying to connect with them (the assumption is that they will have superior connectivity), if they are a higher tier you might expect them to pay you, or to connect for free.

Some of the criteria this tiering system can influence are as follows (to be clear, this is a list of incorrect inferences made by people when looking at the tier of another network):

* Setting the expectation for the average latency that network has to other networks.
* Setting the expectation for the capacity that network has to other networks.
* Setting the expectation for the quality of support that network provides.
* Setting the expectation for how much control that network has, when connectivity issues occur to destinations reached via that network.
* If the connectivity to that network is not free, it can set the expectation for the price range.
* Even if the connectivity is free, connecting networks together is not free; it can set the expectation for which party will cover the interconnection costs.
* Even if the connectivity is free, depending on the traffic ratio it can elevate one network into a position of power over the other.

You might be thinking:

> If the tiering system can help me to establish some base line expectations for all these factors, without having to do lots of research, that sounds like a good thing. What's wrong with that?

Because the tiering system is used as a proxy for actual information, and like all proxies, it can be very inaccurate.

Some examples of the problems with the tiering system:

* It is not an official tiering system with well defined criteria to make it clear which tier a given network belongs to ([more on this later](tier1_asns.md#who-are-the-tier-1s)).
* There is no official list showing which tier a network is in.
* There is no official ability for a non Tier 1 network to become ranked as a Tier 1 network, but a network of any rank can have their rank changed to Tier 2 or 3.
* Networks can't belong to more than one tier (for operators of global networks, the entire network falls into a single tier even though the network might operating differently in different parts of the world).
* It is assumed that all networks in a given tier have similar connectivity properties however, none of the following _very important_ criteria are used for categorisation in the current tiering system (these are just _some_ examples):
    * Average AS path length.
    * Number of directly connected ASNs.
    * The level of connectivity resilience.
    * The geography of interconnection.
    * The internal traffic engineering capabilities.
    * The extent of route filtering.
    * The extent of traffic filtering.
    * Support for BGP communities.
    * Ability to adopt new technologies.
    * Ability to work around peering disputes ([more on this later](#the-exclusivity-of-being-a-tier-1-is-a-curse)).
* It can unjustly punish a network because it's tier rank is higher than another network
* It can unjustly promote a network because it's tier rank is lower than another network

## What Is The Definition of Each Network Tier

The widely accepted but loosely defined categorisation for network tiers is as follows:

* Tier 1: A network which has reachability to all other networks on the public Internet, without having to use another network as a transit provider. This means that a Tier 1 network can reach all other networks on the Internet because any given destination is either a downstream customer of the Tier 1 itself, or a customer of another Tier 1 network which the Tier 1 network has a peering agreement with. This is called a "transit free" network (all destinations are reachable via customers or direct peers, there is no need to transit through a peer to reach the customer cone of the peer's peer).
* Tier 2: A network which has reachability to all other networks on the public Internet, through a mixture of peering agreements and by paying other networks to transit through them to reach their peers. The paid connectivity might be explicitly via a Tier 1, or it might happen implicitly. For example, a Tier 2 might have some free peering, and pay another Tier 2 for upstream connectivity, but because the upstream network is also a Tier 2, if the destination network is not a peer or a customer of that Tier 2, they may be sending the traffic to a Tier 1.
* Tier 3: A network which has reachability to all other networks on the public Internet, only by buying transit connectivity. This means that the network doesn't have free peerings with any other network and must send traffic "up" the tree topology of the Internet.

Wikipedia has definitions with nice diagrams:

* <https://en.wikipedia.org/wiki/Tier_1_network>
* <https://en.wikipedia.org/wiki/Tier_2_network>

The tiering system can also be thought of as a weird kind of tree hierarchy or a weird multi-stage leaf-spine network, where the tree root nodes (super spines) are meshed together;

* All the Tier 1 networks form the "top" level of the tree (meaning the root, or the "super-spine" layer in the leaf-spine analogy). They have full connectivity to all nodes in the tree either via a directly connected downstream node or via the downstream node of a horizontally connected node at the same level in the tree.
* All the Tier 3 networks are the stub/leaf networks right at the bottom of the tree, with nothing downstream of them.
* All the Tier 2 networks are the levels in between the top and bottom, they might have connectivity horizontally with other Tier 2s, downwards to Tier 2s and 3s, and upwards to Tier 1s and 2s.

```text
    ┌───────┬────────┐           
┌───┴──┐ ┌──┴───┐ ┌──┴───┐       
│Tier 1├─┤Tier 1├─┤Tier 1│       
└────┬─┘ └──┬───┘ └──┬───┘       
     │      │        │           
  ┌──┴───┐ ┌┴─────┐ ┌┴─────┐     
  │Tier 2├─┤Tier 2│ │Tier 2│     
  └─────┬┘ └────┬─┘ └┬───┬─┘     
        │       │    │   │       
       ┌┴─────┐┌┴────┴┐ ┌┴─────┐ 
       │Tier 3││Tier 3│ │Tier 2│ 
       └──────┘└──────┘ └┬─────┘ 
                    ┌────┴─┐     
                    │Tier 3│     
                    └──────┘     
```

The problem with this tiering topology is that it is pure theory, the Internet topology is actually a very dense partial-mesh, with peerings across all the tiering level boundaries ([more on this later](../part3/2025/diagrams/README.md)). With the rise of hyperscalers and massive CDN networks, a huge amount of traffic today is delivered from within a metro, and mostly within 1 AS hop within that metro. This is due to extensive public and private peering between source and destination networks, regardless of their "tier".

As mentioned above though, there is no official definition, and the main two/three definitions I hear are:

* A Tier 1 is any network which is transit free.
* A Tier 1 is any network which has full reachability without paying.
* A Tier 1 is any network with both of these properties. This is because any Tier 3 which doesn't pay for it's upstream connectivity would be a Tier 1. Equally, any network which has a connection to all of the Tier 1s without paying, would be transit free and become a Tier 1.

## The Definition of A Tier 1 Network

Let's focus in on the definition of a Tier 1 network for a moment, because this is quite special.

The widely accepted definition of a Tier 1 network, is a network which has reachability to all other networks which are part of the Internet, without having to pay for the connectivity to get there. For example, AS3356 and AS1299 might have established [Settlement Free Interconnection (SFI)](https://en.wikipedia.org/wiki/Peering) between their two networks, therefore they can reach all destinations which they jointly have direct connectivity to via their own network (i.e., their own customers) and all destinations which their peer also has direct connectivity to (the customers of their peer). This is all without having to pay anyone for that connectivity.

There is a group of ASNs (networks) which have settlement free interconnections with each other, _and_ because they are all very large networks, between them, they have connectivity to every network which is part of the Internet. This means that this group of networks with SFIs between each other have free connectivity to all networks. Obviously, operating their own network, and the SFIs, is not free, but they aren't paying anyone external for connectivity. They have connectivity to every network on the Internet, either directly as a customer, or via one of their SFI peers.

This is in contrast to a purchasing ASN which purchases connectivity from a selling ASN, in order to reach all the ASNs the selling ASN is connected to. This product is called IP Transit. An ASN which is buying connectivity from another ASN is said to have an "upstream" (customers are considered "downstreams").

## Except It's Not That Simple

:bulb: If all three tiers have reachability to all other networks on the Internet, then the only difference is what percentage of their reachability each tier is paying for. What's the problem with this? :thinking:

The amount of free or paid connectivity a network has, has absolutely no relation to anything; performance, quality, availability, resiliency, and so on. However, this _is_ the basis for the tiering system (sometimes other factors are added into the mix too, but let's keep it simple for now and stick with this main factor).

* Tier 2 and Tier 3 networks pay for connectivity, Tiers 1s don't (supposedly!).
* If a Tier 2 pays for 99% of their connectivity, are they really different from a Tier 3 who pays for 100% of their connectivity?
* If a Tier 2 pays for only 1% of their connectivity, are they really different from a Tier 1 who pays for 0% of their connectivity?

Where this tiering system really falls down is the Tier 1 category, because there is a little bit more to being categorised as Tier 1 than simply not paying any other parties for connectivity.

In order to meet the Tier 1 criteria of not paying for any connectivity, a network must have settlement free peering with _all_ other Tier 1 networks. This is because peering usually provides access to all customers of a peer network, but not the peers of that peer network, or the customers of the peers of that peer network (otherwise this would meaning transiting through the peer network, breaking the "transit free" criteria). If a network is providing connectivity to more than just it's own customers, then it becomes an upstream provider of the network it is providing this connectivity to. Even if this connectivity is provided for free, the network being provided with the connectivity now has an upstream provider, and Tier 1 networks have no upstream providers (they are transit free), because they all peer with each other.

This means a more exact definition for a Tier 1 network looks something like this:

* The network Has full connectivity to all other networks on the public Internet.
* There are no networks which are upstreams of the network.
* The network does not pay for connectivity to networks who are not a direct customer or reachable via a direct customer.

This combination of factors creates a problems, both for the networks who have Tier 1 status, and for networks who don't...

## What's Wrong With The Tier 1 Definition

There are many problems, here are just some of them...

### Abuse of Privilege

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

### The Exclusivity of Being A Tier 1 Is A Curse

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

### The Current Tier 1s Didn't Earn Their Status

Some of the Tier 1 networks (Orange/France Telecom, DTAG, TI Spark/Seabone) have their roots in the former state owned national telecommunications company of their respective origin countries (there have been many M&As along the way of course). The foundations of these networks were built with tax payers money, but today they no longer seem to want to serve for the good of the people.

Despite having various similarities with say DTAG, why aren't BT or Telstra Tier 1 networks (for clarity, I don't think they should be!)? India and China are both larger than the UK, France, Germany, and Italy; why aren't Bharti Airtel and China Telecom Tier 1s but Orange and TI Sparkle are?

This inherited status of having been around early enough, and large enough (at the time) to establish SFI with the other Tier 1s, is seemingly mistaken for hard data showing how the status was fairly earned. Interestingly, [earlier accounts](https://archive.nanog.org/meetings/nanog45/presentations/Tuesday/Brown_Internet_Peering_N45.pdf) of which networks are the Tier 1s, contain a different set of networks to the generally accepted list of today.

### Hot Potato Routing

The Internet is massively reliant on PNIs and embedded caches, in terms of peak traffic load (and to a lesser extent, IXPs). The bulk of traffic is not carrier via IP Transit. Tier 1 networks may peer with a non Tier 1 network (albeit only a select handful) for free, on the proviso that the Tier 1 only provides reachability to its on-net customer prefixes and if the peer wants transit connectivity, they need to pay for it. But they are fairly well incentivised to not peer other networks.

As already mentioned, if another network could peer with all Tier 1s, that network implicitly becomes a new Tier 1, devaluing this status based purely on exclusivity, as more an more networks achieve it. In addition, for networks which sell IP Transit as a service, it is in their best interest to peer with as few other networks as possible, because every peer is a potential customer they can no longer have. This creates a chicken and egg problem though; nobody wants to buy connectivity from a network which isn't well peered. However, the more a network peers, the smaller the pool of potential customers becomes. And it's not just about the number of networks, but the type too; access networks want connectivity to content networks and vice versa. Somehow a network selling IP connectivity needs to develop a large amount of customers with as few peers as possible, in order to achieve maximal revenues. Simply having Tier 1 status breaks this chicken and egg cycle; other network operators want to buy from Tier 1s de facto, regardless of whether that Tier 1 actually has the best connectivity for the requirement, and peering with a Tier 1 is (usually) not an option, so paying is the only way forward.

If a company wants to make it their business to sell IP connectivity, and thus avoid free peering, that is their choice. However, many Tier 1s operate global networks with high international connectivity costs, and due to the never ending pressure to reduce the price per bit, they are forced to operate a [hot potato routing](https://en.wikipedia.org/wiki/Hot-potato_routing) model. The result is that the customer pays for transit connectivity which doesn't guarantee good quality connectivity, because the Tier 1 isn't densely peering in the destination market. Compare this to a Tier 2 with an open peering policy; many Tier 2s have much richer and denser peering in their home markets than any Tier 1 could achieve when coming in from the outside. As a result, Tier 2s can operate cold potato routing within their home market and provide superior connectivity.

One notable exception to this is Hurricane Electric (AS6939), they seem to want to peer with anyone and everyone. It is hard to understand how they gain customers, but they do have an [extremely well peered network](https://bgp.tools/rankings/all?sort=peering) as a result of their open peering policy.
