from collections import OrderedDict
from typing import Optional, Tuple

from ..en import Provider as AddressProvider


class Provider(AddressProvider):
    city_prefixes = ("North", "East", "West", "South", "New", "Lake", "Port")

    city_suffixes = (
        "town",
        "ton",
        "land",
        "ville",
        "berg",
        "burgh",
        "borough",
        "bury",
        "view",
        "port",
        "mouth",
        "stad",
        "furt",
        "chester",
        "mouth",
        "fort",
        "haven",
        "side",
        "shire",
    )

    building_number_formats = ("#####", "####", "###")

    street_suffixes = (
        "Alley",
        "Avenue",
        "Branch",
        "Bridge",
        "Brook",
        "Brooks",
        "Burg",
        "Burgs",
        "Bypass",
        "Camp",
        "Canyon",
        "Cape",
        "Causeway",
        "Center",
        "Centers",
        "Circle",
        "Circles",
        "Cliff",
        "Cliffs",
        "Club",
        "Common",
        "Corner",
        "Corners",
        "Course",
        "Court",
        "Courts",
        "Cove",
        "Coves",
        "Creek",
        "Crescent",
        "Crest",
        "Crossing",
        "Crossroad",
        "Curve",
        "Dale",
        "Dam",
        "Divide",
        "Drive",
        "Drive",
        "Drives",
        "Estate",
        "Estates",
        "Expressway",
        "Extension",
        "Extensions",
        "Fall",
        "Falls",
        "Ferry",
        "Field",
        "Fields",
        "Flat",
        "Flats",
        "Ford",
        "Fords",
        "Forest",
        "Forge",
        "Forges",
        "Fork",
        "Forks",
        "Fort",
        "Freeway",
        "Garden",
        "Gardens",
        "Gateway",
        "Glen",
        "Glens",
        "Green",
        "Greens",
        "Grove",
        "Groves",
        "Harbor",
        "Harbors",
        "Haven",
        "Heights",
        "Highway",
        "Hill",
        "Hills",
        "Hollow",
        "Inlet",
        "Inlet",
        "Island",
        "Island",
        "Islands",
        "Islands",
        "Isle",
        "Isle",
        "Junction",
        "Junctions",
        "Key",
        "Keys",
        "Knoll",
        "Knolls",
        "Lake",
        "Lakes",
        "Land",
        "Landing",
        "Lane",
        "Light",
        "Lights",
        "Loaf",
        "Lock",
        "Locks",
        "Locks",
        "Lodge",
        "Lodge",
        "Loop",
        "Mall",
        "Manor",
        "Manors",
        "Meadow",
        "Meadows",
        "Mews",
        "Mill",
        "Mills",
        "Mission",
        "Mission",
        "Motorway",
        "Mount",
        "Mountain",
        "Mountain",
        "Mountains",
        "Mountains",
        "Neck",
        "Orchard",
        "Oval",
        "Overpass",
        "Park",
        "Parks",
        "Parkway",
        "Parkways",
        "Pass",
        "Passage",
        "Path",
        "Pike",
        "Pine",
        "Pines",
        "Place",
        "Plain",
        "Plains",
        "Plains",
        "Plaza",
        "Plaza",
        "Point",
        "Points",
        "Port",
        "Port",
        "Ports",
        "Ports",
        "Prairie",
        "Prairie",
        "Radial",
        "Ramp",
        "Ranch",
        "Rapid",
        "Rapids",
        "Rest",
        "Ridge",
        "Ridges",
        "River",
        "Road",
        "Road",
        "Roads",
        "Roads",
        "Route",
        "Row",
        "Rue",
        "Run",
        "Shoal",
        "Shoals",
        "Shore",
        "Shores",
        "Skyway",
        "Spring",
        "Springs",
        "Springs",
        "Spur",
        "Spurs",
        "Square",
        "Square",
        "Squares",
        "Squares",
        "Station",
        "Station",
        "Stravenue",
        "Stravenue",
        "Stream",
        "Stream",
        "Street",
        "Street",
        "Streets",
        "Summit",
        "Summit",
        "Terrace",
        "Throughway",
        "Trace",
        "Track",
        "Trafficway",
        "Trail",
        "Trail",
        "Tunnel",
        "Tunnel",
        "Turnpike",
        "Turnpike",
        "Underpass",
        "Union",
        "Unions",
        "Valley",
        "Valleys",
        "Via",
        "Viaduct",
        "View",
        "Views",
        "Village",
        "Village",
        "Villages",
        "Ville",
        "Vista",
        "Vista",
        "Walk",
        "Walks",
        "Wall",
        "Way",
        "Ways",
        "Well",
        "Wells",
    )

    postcode_formats = ("#####", "#####-####")

    states = (
        "Alabama",
        "Alaska",
        "Arizona",
        "Arkansas",
        "California",
        "Colorado",
        "Connecticut",
        "Delaware",
        "Florida",
        "Georgia",
        "Hawaii",
        "Idaho",
        "Illinois",
        "Indiana",
        "Iowa",
        "Kansas",
        "Kentucky",
        "Louisiana",
        "Maine",
        "Maryland",
        "Massachusetts",
        "Michigan",
        "Minnesota",
        "Mississippi",
        "Missouri",
        "Montana",
        "Nebraska",
        "Nevada",
        "New Hampshire",
        "New Jersey",
        "New Mexico",
        "New York",
        "North Carolina",
        "North Dakota",
        "Ohio",
        "Oklahoma",
        "Oregon",
        "Pennsylvania",
        "Rhode Island",
        "South Carolina",
        "South Dakota",
        "Tennessee",
        "Texas",
        "Utah",
        "Vermont",
        "Virginia",
        "Washington",
        "West Virginia",
        "Wisconsin",
        "Wyoming",
    )
    states_abbr = (
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "DC",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
    )

    states_postcode = {
        "AL": (35004, 36925),
        "AK": (99501, 99950),
        "AZ": (85001, 86556),
        "AR": (71601, 72959),
        "CA": (90001, 96162),
        "CO": (80001, 81658),
        "CT": (6001, 6389),
        "DE": (19701, 19980),
        "DC": (20001, 20039),
        "FL": (32004, 34997),
        "GA": (30001, 31999),
        "HI": (96701, 96898),
        "ID": (83201, 83876),
        "IL": (60001, 62999),
        "IN": (46001, 47997),
        "IA": (50001, 52809),
        "KS": (66002, 67954),
        "KY": (40003, 42788),
        "LA": (70001, 71232),
        "ME": (3901, 4992),
        "MD": (20812, 21930),
        "MA": (1001, 2791),
        "MI": (48001, 49971),
        "MN": (55001, 56763),
        "MS": (38601, 39776),
        "MO": (63001, 65899),
        "MT": (59001, 59937),
        "NE": (68001, 68118),
        "NV": (88901, 89883),
        "NH": (3031, 3897),
        "NJ": (7001, 8989),
        "NM": (87001, 88441),
        "NY": (10001, 14905),
        "NC": (27006, 28909),
        "ND": (58001, 58856),
        "OH": (43001, 45999),
        "OK": (73001, 73199),
        "OR": (97001, 97920),
        "PA": (15001, 19640),
        "RI": (2801, 2940),
        "SC": (29001, 29948),
        "SD": (57001, 57799),
        "TN": (37010, 38589),
        "TX": (75503, 79999),
        "UT": (84001, 84784),
        "VT": (5001, 5495),
        "VA": (22001, 24658),
        "WA": (98001, 99403),
        "WV": (24701, 26886),
        "WI": (53001, 54990),
        "WY": (82001, 83128),
        # Territories & freely-associated states
        # incomplete ranges with accurate subsets - https://www.geonames.org/postalcode-search.html
        "AS": (96799, 96799),
        "FM": (96941, 96944),
        "GU": (96910, 96932),
        "MH": (96960, 96970),
        "MP": (96950, 96952),
        "PW": (96940, 96940),
        "PR": (600, 799),
        "VI": (801, 805),
    }

    territories_abbr = (
        "AS",
        "GU",
        "MP",
        "PR",
        "VI",
    )

    # Freely-associated states (sovereign states; members of COFA)
    # https://en.wikipedia.org/wiki/Compact_of_Free_Association
    freely_associated_states_abbr = (
        "FM",
        "MH",
        "PW",
    )

    known_usps_abbr = states_abbr + territories_abbr + freely_associated_states_abbr

    military_state_abbr = ("AE", "AA", "AP")

    military_ship_prefix = ("USS", "USNS", "USNV", "USCGC")

    military_apo_format = "PSC ####, Box ####"

    military_dpo_format = "Unit #### Box ####"

    city_formats = (
        "{{city_prefix}} {{first_name}}{{city_suffix}}",
        "{{city_prefix}} {{first_name}}",
        "{{first_name}}{{city_suffix}}",
        "{{last_name}}{{city_suffix}}",
    )

    street_name_formats = (
        "{{first_name}} {{street_suffix}}",
        "{{last_name}} {{street_suffix}}",
    )

    street_address_formats = (
        "{{building_number}} {{street_name}}",
        "{{building_number}} {{street_name}} {{secondary_address}}",
    )

    address_formats = OrderedDict(
        (
            ("{{street_address}}\n{{city}}, {{state_abbr}} {{postcode}}", 25.0),
            #  military address formatting.
            ("{{military_apo}}\nAPO {{military_state}} {{postcode}}", 1.0),
            (
                "{{military_ship}} {{last_name}}\nFPO {{military_state}} {{postcode}}",
                1.0,
            ),
            ("{{military_dpo}}\nDPO {{military_state}} {{postcode}}", 1.0),
        )
    )

    secondary_address_formats = ("Apt. ###", "Suite ###")

    def city_prefix(self) -> str:
        return self.random_element(self.city_prefixes)

    def secondary_address(self) -> str:
        return self.numerify(self.random_element(self.secondary_address_formats))

    def administrative_unit(self) -> str:
        return self.random_element(self.states)

    state = administrative_unit

    def state_abbr(
        self,
        include_territories: bool = True,
        include_freely_associated_states: bool = True,
    ) -> str:
        """
        :returns: A random two-letter USPS postal code

        By default, the resulting code may abbreviate any of the fifty states,
        five US territories, or three freely-associating sovereign states.

        :param include_territories: If True, territories will be included.
            If False, US territories will be excluded.
        :param include_freely_associated_states: If True, freely-associated states will be included.
            If False, sovereign states in free association with the US will be excluded.
        """
        abbreviations: Tuple[str, ...] = self.states_abbr
        if include_territories:
            abbreviations += self.territories_abbr
        if include_freely_associated_states:
            abbreviations += self.freely_associated_states_abbr
        return self.random_element(abbreviations)

    def postcode(self) -> str:
        return "%05d" % self.generator.random.randint(501, 99950)

    def zipcode_plus4(self) -> str:
        return "%s-%04d" % (self.zipcode(), self.generator.random.randint(1, 9999))

    def postcode_in_state(self, state_abbr: Optional[str] = None) -> str:
        """
        :returns: A random postcode within the provided state abbreviation

        :param state_abbr: A state abbreviation
        """
        if state_abbr is None:
            state_abbr = self.random_element(self.states_abbr)

        if state_abbr in self.known_usps_abbr:
            postcode = "%d" % (
                self.generator.random.randint(
                    self.states_postcode[state_abbr][0],
                    self.states_postcode[state_abbr][1],
                )
            )

            # zero left pad up until desired length (some have length 3 or 4)
            target_postcode_len = 5
            current_postcode_len = len(postcode)
            if current_postcode_len < target_postcode_len:
                pad = target_postcode_len - current_postcode_len
                postcode = f"{'0'*pad}{postcode}"

            return postcode

        else:
            raise Exception("State Abbreviation not found in list")

    def military_ship(self) -> str:
        """
        :example: 'USS'
        """
        return self.random_element(self.military_ship_prefix)

    def military_state(self) -> str:
        """
        :example: 'APO'
        """
        return self.random_element(self.military_state_abbr)

    def military_apo(self) -> str:
        """
        :example: 'PSC 5394 Box 3492
        """
        return self.numerify(self.military_apo_format)

    def military_dpo(self) -> str:
        """
        :example: 'Unit 3333 Box 9342'
        """
        return self.numerify(self.military_dpo_format)

    # Aliases
    def zipcode(self) -> str:
        return self.postcode()

    def zipcode_in_state(self, state_abbr: Optional[str] = None) -> str:
        return self.postcode_in_state(state_abbr)

    def postalcode(self) -> str:
        return self.postcode()

    def postalcode_in_state(self, state_abbr: Optional[str] = None) -> str:
        return self.postcode_in_state(state_abbr)

    def postalcode_plus4(self) -> str:
        return self.zipcode_plus4()
