from .. import Provider as InternetProvider


class Provider(InternetProvider):
    tlds = ("com", "com", "com", "net", "org", "no", "no", "no", "no", "no")

    replacements = (
        ("æ", "ae"),
        ("Æ", "Ae"),
        ("ø", "oe"),
        ("Ø", "Oe"),
        ("å", "aa"),
        ("Å", "Aa"),
        ("ä", "ae"),
        ("Ä", "Ae"),
        ("ö", "oe"),
        ("Ö", "Oe"),
        ("ü", "ue"),
        ("Ü", "Ue"),
    )
