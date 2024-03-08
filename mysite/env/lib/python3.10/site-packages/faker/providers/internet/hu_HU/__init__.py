from .. import Provider as InternetProvider


class Provider(InternetProvider):
    free_email_domains = (
        "gmail.com",
        "hotmail.com",
        "yahoo.com",
    )

    tlds = (
        "hu",
        "com",
        "com.hu",
        "info",
        "org",
        "net",
        "biz",
    )

    replacements = (
        ("ö", "o"),
        ("ü", "u"),
        ("á", "a"),
        ("é", "e"),
        ("í", "i"),
        ("ó", "i"),
        ("ő", "o"),
        ("ú", "u"),
        ("ű", "u"),
    )
