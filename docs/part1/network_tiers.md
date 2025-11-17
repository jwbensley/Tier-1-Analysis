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
    * Ability to work around peering disputes ([more on this later](tier1_problems.md#the-exclusivity-of-being-a-tier-1-is-a-curse)).
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

The problem with this tiering topology is that it is pure theory, the Internet topology is actually a very dense partial-mesh, with peerings across all the tiering level boundaries ([see these diagrams](../part3/2025/diagrams/README.md)). With the rise of hyperscalers and massive CDN networks, a huge amount of traffic today is delivered from within a metro, and mostly within 1 AS hop within that metro. This is due to extensive public and private peering between source and destination networks, regardless of their "tier".

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
