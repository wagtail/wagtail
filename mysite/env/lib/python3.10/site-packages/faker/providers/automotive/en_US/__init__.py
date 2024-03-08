from .. import Provider as AutomotiveProvider


class Provider(AutomotiveProvider):
    """Implement automotive provider for ``en_US`` locale.

    Sources:

    - https://en.wikipedia.org/wiki/United_States_license_plate_designs_and_serial_formats
    """

    license_formats = (
        # Alabama
        "#??####",
        "##??###",
        # Alaska
        "### ???",
        # American Samoa
        "####",
        # Arizona
        "???####",
        # Arkansas
        "### ???",
        "###???",
        # California
        "#???###",
        # Colarado
        "###-???",
        "???-###",
        # Conneticut
        "###-???",
        # Delaware
        "######",
        # DC
        "??-####",
        # Florda
        "??? ?##",
        "### ???",
        "?## #??",
        "### #??",
        # Georgia
        "???####",
        # Guam
        "?? ####",
        # Hawaii
        "??? ###",
        "H?? ###",
        "Z?? ###",
        "K?? ###",
        "L?? ###",
        "M?? ###",
        # Idaho
        "? ######",
        "#? #####",
        "#? ?####",
        "#? ??###",
        "#? #?#???",
        "#? ####?",
        "##? ####",
        # Illinois
        "?? #####",
        "??# ####",
        # Indiana
        "###?",
        "###??",
        "###???",
        # Iowa
        "??? ###",
        # Kansas
        "### ???",
        # Kentucky
        "### ???",
        # Louisiana
        "### ???",
        # Maine
        "#### ??",
        # Maryland
        "#??####",
        # Massachusetts
        "#??? ##",
        "#?? ###",
        "### ??#",
        "##? ?##",
        # Michigan
        "### ???",
        "#?? ?##",
        # Minnesota
        "###-???",
        # Mississippi
        "??? ###",
        # Missouri
        "??# ?#?",
        # Montana
        "#-#####?",
        "##-####?",
        # Nebraska
        "??? ###",
        "#-?####",
        "##-?###",
        "##-??##",
        # Nevada
        "##?•###",
        # New Hampshire
        "### ####",
        # New Jersey
        "?##-???",
        # New Mexico
        "###-???",
        "???-###",
        # New York
        "???-####",
        # North Carolina
        "###-????",
        # North Dakota
        "### ???",
        # Nothern Mariana Islands
        "??? ###",
        # Ohio
        "??? ####",
        # Oklahoma
        "???-###",
        # Oregon
        "### ???",
        # Pennsylvania
        "???-####",
        # Peurto Rico
        "???-###",
        # Rhode Island
        "###-###",
        # South Carolina
        "### #??",
        # South Dakota
        "#?? ###",
        "#?? ?##",
        "##? ###",
        "##? ?##",
        "##? ??#",
        # Tennessee
        "?##-##?",
        # Texas
        "???-####",
        # Utah
        "?## #??",
        "?## #??",
        # Vermont
        "??? ###",
        "##??#",
        "#??##",
        "###?#",
        "#?###",
        # US Virgin Islands
        "??? ###",
        # Virginia
        "???-####",
        # Washington
        "???####",
        "###-???",
        # West Virginia
        "#?? ###",
        "??? ###",
        # Wisconsin
        "???-####",
        "###-???",
        # Wyoming
        "#-#####",
        "#-####?",
        "##-#####",
    )
