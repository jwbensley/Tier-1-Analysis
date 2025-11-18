---
parent: Reports
nav_order: 2
---

# 2025 DFZ Diagrams

This folder contains diagrams of the DFZ. Each point on the graph is an ASN which is not a stub ASN (a edge ASN with nothing behind it). This is because there are a lot of stub ASNs and including them not only causes the diagram to be so large that each ASN is just a tiny speck, but because they aren't very "interesting" ASNs topologically.

A few different diagrams have been rendered from the same data. The "small" images below probably will open in your browser or with your operating systems default image viewer. The linked "large" images _might_ open in your browser, but zooming in and out doesn't work for me, or opening with your operating systems default image viewer _might_ work (it doesn't for me). I view them with ease in [GIMP](https://www.gimp.org/).

The "nodesizes" images have each ASN centered on a blue dot. The size of the blue dot is based on the number of connections that ASN has.

* 8-12MBs per image:
  * [graph_87860_60_60_60_kamada.png](https://github.com/jwbensley/Tier-1-Analysis/blob/main/docs/part3/2025/diagrams/graph_87860_60_60_60_kamada.png)
  * [graph_87860_60_60_60_kamada_nodesizes.png](https://github.com/jwbensley/Tier-1-Analysis/blob/main/docs/part3/2025/diagrams/graph_87860_60_60_60_kamada_nodesizes.png)
  * [graph_87860_60_60_60_spring.png](https://github.com/jwbensley/Tier-1-Analysis/blob/main/docs/part3/2025/diagrams/graph_87860_60_60_60_spring.png)
  * [graph_87860_60_60_60_spring_nodesizes.png](https://github.com/jwbensley/Tier-1-Analysis/blob/main/docs/part3/2025/diagrams/graph_87860_60_60_60_spring_nodesizes.png)
* 125-175MBs per image:
  * [graph_87860_150_150_150_kamada.png](https://github.com/jwbensley/Tier-1-Analysis/blob/main/docs/part3/2025/diagrams/graph_87860_150_150_150_kamada.png)
  * [graph_87860_150_150_150_kamada_nodesizes.png](https://github.com/jwbensley/Tier-1-Analysis/blob/main/docs/part3/2025/diagrams/graph_87860_150_150_150_kamada_nodesizes.png)
  * [graph_87860_150_150_150_spring.png](https://github.com/jwbensley/Tier-1-Analysis/blob/main/docs/part3/2025/diagrams/graph_87860_150_150_150_spring.png)
  * [graph_87860_150_150_150_spring_nodesizes.png](https://github.com/jwbensley/Tier-1-Analysis/blob/main/docs/part3/2025/diagrams/graph_87860_150_150_150_spring_nodesizes.png)

If you want to try and render these yourself using the scripts in this repo, be aware that this is requires several hours of rendering time and about 20GBs of RAM.
