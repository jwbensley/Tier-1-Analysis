import ipaddress
from ipaddress import IPv4Network, IPv6Network


class BogonPrefixes:
    """
    Class to check if an IP subnet is a bogon address.
    """

    BOGON_V4_NETS = [
        IPv4Network("0.0.0.0/8"),  # RFC 1700
        IPv4Network("10.0.0.0/8"),  # RFC 1918
        IPv4Network("100.64.0.0/10"),  # RFC 6598
        IPv4Network("127.0.0.0/8"),  # RFC 6890
        IPv4Network("169.254.0.0/16"),  # RFC 6890
        IPv4Network("172.16.0.0/12"),  # RFC 1918
        IPv4Network("192.0.0.0/29"),  # RFC 6333
        IPv4Network("192.0.2.0/24"),  # RFC 5737 IPv4
        IPv4Network("192.88.99.0/24"),  # RFC 3068
        IPv4Network("192.168.0.0/16"),  # RFC 1918
        IPv4Network("198.18.0.0/15"),  # RFC 2544
        IPv4Network("198.51.100.0/24"),  # RFC 5737 IPv4
        IPv4Network("203.0.113.0/24"),  # RFC 5737 IPv4
        IPv4Network("224.0.0.0/4"),  # RFC 5771
        IPv4Network("240.0.0.0/4"),  # RFC 6890
    ]

    BOGON_V6_NETS = [
        IPv6Network("::/8"),  # RFC 4291
        IPv6Network("0100::/64"),  # RFC 6666
        IPv6Network("2001:2::/48"),  # RFC 5180
        IPv6Network("2001:10::/28"),  # RFC 4843
        IPv6Network("2001:db8::/32"),  # RFC 3849
        IPv6Network("2002::/16"),  # RFC 7526
        IPv6Network("3ffe::/16"),  # RFC 3701
        IPv6Network("fc00::/7"),  # RFC 4193
        IPv6Network("fe00::/9"),  # IETF Reserved
        IPv6Network("fe80::/10"),  # RFC 4291
        IPv6Network("fec0::/10"),  # RFC 3879
        IPv6Network("ff00::/8"),  # RFC 4291
    ]

    @staticmethod
    def is_bogon(subnet: str) -> bool:
        """
        Return True if IP prefix is in a v4  or v6 bogon range, else False.
        Expects CIDR notation as string.
        """
        ip_net = ipaddress.ip_network(subnet)
        if isinstance(ip_net, IPv4Network):
            for bogon_v4_net in BogonPrefixes.BOGON_V4_NETS:
                if ip_net.subnet_of(bogon_v4_net):
                    return True
            return False
        else:
            for bogon_v6_net in BogonPrefixes.BOGON_V6_NETS:
                if ip_net.subnet_of(bogon_v6_net):
                    return True
            return False
