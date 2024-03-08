from collections import OrderedDict

from .. import Provider as InternetProvider


class Provider(InternetProvider):
    free_email_domains = (
        "hotmail.com",
        "gmail.com",
        "outlook.com",
        "yahoo.com",
        "ymail.com",
        "kon.in.th",
        "icloud.com",
        "protonmail.com",
    )

    tlds = OrderedDict(
        (
            ("in.th", 100),
            ("co.th", 80),
            ("go.th", 40),
            ("or.th", 40),
            ("ac.th", 20),
            ("net.th", 10),
            ("mi.th", 5),
            ("co", 10),
            ("net", 20),
            ("com", 150),
            ("org", 50),
        ),
    )
