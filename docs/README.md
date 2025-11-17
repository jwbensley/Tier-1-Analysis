# Evaluating Network Tiers

## Intro

The archaic tiering system used for ranking networks that form the Internet implies that Tier 1 networks are the best ("best" will be [clarified later](part1/network_tiers.md)) at providing connectivity, followed by Tier 2 networks, and then finally Tier 3 networks.

The industry has been saying for years that this isn't true. Despite this, not only do many people still believe it, many people see no reason _not_ to believe it, nor to try and put an end to this broken tiering system.

The content in this repository aims to provide information showing how this tiering system is fundamentally broken, to highlight that it should be abandoned ASAP, and that the extended to which the marketing teams of Tier 1 networks have succeeded in pulling the wool over our eyes.

To do this, BGP data from the most interconnected networks in the world will be gathered, analysed and compared.

> [!NOTE]
> I'm going to do quite a bit of shitting on the Tier 1 networks however, one very important (to me) point of note; I know personally people who work at some of the networks being analysed. They are great engineers, much smarter than me. I am not criticising the technical operations or design of these networks. I am criticising the economic and political choices made by the companies, and the connectivity market at large.

## The Problems with Network Tiers

In this part the problem with the tiering system is discussed, and a list of networks for analysis is compiled:

* [What is the network tiering system and what's wrong with it?](part1/network_tiers.md)
* [Who are the tier 1 networks?](part1/tier1_asns.md)
* [Identifying other networks to compare with tier 1s](part1/asns_of_interest.md)

## Getting and Processing the Data

In this part the problem with getting usable data is demonstrated, and what data processing caveats exist:

* [Data source problems](part2/data_source_problems.md)
* [Getting the data](part2/getting_the_data.md)
* [Processing the data](part2/processing_the_data.md)

## Reports

Below is a list of reports produced, each discusses what was found in the gathered and processes BGP data.

Q3-2025 is the first time gathering and analysing the data, but the process is fully automated so it _might_ become a yearly event.

An important point of note is that data was gathered an analysed for a single day to give a point-in-time reference. The DFZ is constantly changing, but at a very slow pace. If you look again, the numbers will have changed, but critically, a few weeks or one or two months later, the numbers won't have changed dramatically. My personal opinion is that the data in the reports are OK if used for macro level analysis, but not micro level.

* [Q3-2025 Report](part3/2025/README.md)

## Credits

I owe thanks to the following people for helping me to produce my initial 2025 report. Some of them don't know they helped though. Whilst some people donated data to help explicitly with comparing the connectivity of ASNs, others I was simply chatting with about weird observations in the DFZ, and they maybe said something that put a new idea in my head, and contributed implicitly or unknowingly, but no less valuably.

In alphabetical order:

* Alistair Mackenzie
* Christian Seitz
* Dan Peachy
* Jody Botham
* Matthias Ordner
* Noah van der Aa
* Philipp Kern
* Rob Evens
* Tommy Croghan
* Tyler Leeds
* Warren Hall

## Reproducibility and Transparency

> [!IMPORTANT]
> Some of the information provided is hard data, for example data gathered from BGP, which is publicly available so that anyone can see for themselves. Some of it is anecdotal and information not easily verifiable via public sources, which I have gathered based on private chats at conferences, having been involved in buying and selling such services, writing and responding to RFPs, reading through MSAs, and generally operating networks for nearly two decades. I have tried to make the use of publicly verifiable facts vs anecdotes clear throughout.

Another factor of reproducibility is the ability for someone else to run the code. Yes, this is written in Python which means it's very slow and very memory inefficient when run. This is a spare time project _and_ not about real-time analysis. This means I need to optimise for reducing developer time, not run time. If you want to run the code, it takes a full night and about 50GBs of RAM. I'm slowly transitioning to rust but I saved _a lot_ of time by writing this in Python, deal with it.

## Disclaimer about DFZ Analyses

> [!WARNING]
> Anyone who tells you something is a hard fact about the DFZ is either lying or doesn't know what they're talking about. A fundamental property of the DFZ is that there is no one single DFZ. The information provided in the reports in this repo provide approximations, indications, suggestions, and never exact 100% undeniable facts. Don't make any decisions or formulate any opinions based on the data found in this repo. I take no responsibility for any outcomes that result from someone reading the data in this repo.
