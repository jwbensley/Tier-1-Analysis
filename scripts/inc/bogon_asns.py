class BogonAsns:
    assigned_asns: set[int]

    @classmethod
    def load_allocated_asns(cls, filename: str) -> None:
        BogonAsns.assigned_asns = set()

        for line in open(filename).readlines():
            values = line.split("|")

            # Country code
            cc = values[1].upper()
            if cc == "*":
                continue

            # Resource type
            if values[2].lower() != "asn":
                continue

            # Status
            if values[6].lower() != "assigned":
                continue

            base_asn = int(values[3])
            asn_range = int(values[4])

            for asn in range(base_asn, base_asn + asn_range):
                if asn in BogonAsns.assigned_asns:
                    raise ValueError(f"ASN found more than once: {asn}")
                BogonAsns.assigned_asns.add(asn)

        print(f"Loaded {len(BogonAsns.assigned_asns)} assigned ASNs")

    @classmethod
    def is_bogon(cls, asn: int) -> bool:
        return asn not in BogonAsns.assigned_asns
