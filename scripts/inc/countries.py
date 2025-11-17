import pycountry_convert as pc


def cc_to_continent_name(cc: str) -> str:
    continent_code: str = pc.country_alpha2_to_continent_code(cc)
    continent_name: str = pc.convert_continent_code_to_continent_name(
        continent_code
    )
    return continent_name


def get_asn_to_continent_mappings(filename: str) -> dict[int, str]:
    """
    Return mappings of AS number to continent name from NRO allocation file.
    Requires the path to the NRO allocations file.
    """
    mappings: dict[int, str] = {}

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
            if asn in mappings:
                raise ValueError(f"ASN found more than once: {asn}")

            # Special cases
            if cc == "AP":
                """
                At the time of writing there are only two ASNs with this code.
                They are both assigned to APNIC but are both allocated to
                countries operating in the USA.
                """
                mappings[asn] = "North America"
            elif cc == "EU":
                """
                Many ASNs have this code. They seem to be ASNs assigned to RIPE,
                used by companies all over Europe.
                """
                mappings[asn] = "Europe"
            elif cc == "SX":
                # Philipsburg
                mappings[asn] = "South America"
            elif cc == "TL":
                # Timor-Leste
                mappings[asn] = "Asia"
            elif cc == "VA":
                # Vatican City
                mappings[asn] = "Europe"
            else:
                mappings[asn] = cc_to_continent_name(cc)

    print(f"Mapped {len(mappings.keys())} ASNs to continents")
    return mappings
