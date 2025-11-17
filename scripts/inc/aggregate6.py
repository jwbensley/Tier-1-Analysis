"""
* Inline the main function from the aggregate6 module
* Replace py-radix with Pytricia
* Inline the certain functions from the ipaddress module

Load a full DFZ table into a py-radix tree and aggregate using aggregate6:

Populating py-radix trees...
Loaded 1001894 v4 prefixes and 224704 v6 prefixes
Duration: 1.3851726055145264

Aggregating py-radix trees...
Aggregated to 162315 v4 prefixes and 58546 v6 prefixes
Duration: 41.362250328063965


This module, which loads a full DFZ table into a pytricia tree,
and aggregates using the bastard code below:

Populating pytricia trees...
Loaded 1001894 v4 prefixes and 224704 v6 prefixes
Duration: 0.4689810276031494

Aggregating pytricia trees...
Aggregated to 162315 v4 prefixes and 58546 v6 prefixes
Duration: 24.281097173690796
"""

import pytricia


def int_to_ip(ip_int: int, size: int) -> str:
    if size == 32:
        return '.'.join(
            str((ip_int >> (i * 8)) & 0xFF) for i in range(3, -1, -1)
        )
    else:
        hex_str = '%032x' % ip_int
        hextets = ['%x' % int(hex_str[x : x + 4], 16) for x in range(0, 32, 4)]
        return ':'.join(hextets)


def ip_to_int(ip: str, size: int) -> int:
    if size == 32:
        octets = list(map(int, ip.split(".")))
        return int(
            f"{octets[0] << 24 | octets[1] << 16 | octets[2] << 8 | octets[3]:032b}",
            2,
        )
    else:

        skip_index = None
        parts = ip.split(':')

        # Check for presence of "::"
        for i in range(1, len(parts) - 1):
            if not parts[i]:
                skip_index = i
                break

        # parts_hi is the number of parts to copy from above/before the '::'
        # parts_lo is the number of parts to copy from below/after the '::'
        if skip_index is not None:
            parts_hi = skip_index
            parts_lo = len(parts) - skip_index - 1
            if not parts[0]:
                parts_hi -= 1
            if not parts[-1]:
                parts_lo -= 1
            parts_skipped = 8 - (parts_hi + parts_lo)
        else:
            # Otherwise, allocate the entire address to parts_hi.
            parts_hi = len(parts)
            parts_lo = 0
            parts_skipped = 0

        # Now, parse the hextets into a 128-bit integer.
        ip_int = 0
        for i in range(parts_hi):
            ip_int <<= 16
            ip_int |= int(parts[i], 16)
        ip_int <<= 16 * parts_skipped
        for i in range(-parts_lo, 0):
            ip_int <<= 16
            ip_int |= int(parts[i], 16)

        return ip_int


def aggregate_pyt(tree: pytricia.PyTricia, size: int) -> list[str]:
    # phase1 removes any supplied prefixes which are superfluous because
    # they are already included in another supplied prefix. For example,
    # 2001:67c:208c:10::/64 would be removed if 2001:67c:208c::/48 was
    # also supplied.
    n_tree = pytricia.PyTricia(size)

    for prefix in tree:
        parent = prefix
        while tree.parent(parent):
            parent = tree.parent(parent)
        n_tree.insert(parent, None)

    potential = len(n_tree)

    while potential:
        # phase2 identifies adjacent prefixes that can be combined under a
        # single, shorter-length prefix. For example, 2001:67c:208c::/48 and
        # 2001:67c:208d::/48 can be combined into the single prefix
        # 2001:67c:208c::/47.
        potential = 0
        for prefix in list(n_tree):
            base_net, base_mask = prefix.split("/")

            """
            Don't need to cater for this scenario because elsewhere we ensure
            no default routes are present
            """
            # if base_mask == "0":
            #    return prefix

            base_net_int = ip_to_int(base_net, size)
            base_mask_int = int(base_mask)

            parent_mask_int = base_mask_int - 1
            parent_mask = str(parent_mask_int)
            parent_mask_bin = ("1" * parent_mask_int) + (
                "0" * (size - parent_mask_int)
            )
            parent_net_int = base_net_int & int(parent_mask_bin, 2)
            parent_net = int_to_ip(parent_net_int, size)

            next_net_start_bin = (
                ("0" * base_mask_int) + "1" + ("0" * (size - base_mask_int))
            )
            second_subnet_int = parent_net_int | int(next_net_start_bin, 2)
            second_subnet = int_to_ip(second_subnet_int, size)

            prefix_1 = parent_net + "/" + base_mask
            prefix_2 = second_subnet + "/" + base_mask
            parent = parent_net + "/" + parent_mask

            if n_tree.has_key(prefix_1) and n_tree.has_key(prefix_2):
                n_tree.delete(prefix_1)
                n_tree.delete(prefix_2)
                n_tree.insert(parent, None)
                potential += 1

    return list(n_tree)
