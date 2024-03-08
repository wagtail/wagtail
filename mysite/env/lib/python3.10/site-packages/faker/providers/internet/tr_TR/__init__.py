from .. import Provider as InternetProvider


class Provider(InternetProvider):
    free_email_domains = (
        "hotmail.com",
        "gmail.com",
        "yahoo.com",
        "yandex.com",
        "yaani.com",
        "outlook.com",
    )
    tlds = ("com", "net", "org", "tr")

    replacements = (
        ("ı", "i"),
        ("ğ", "g"),
        ("ü", "u"),
        ("ş", "s"),
        ("ö", "o"),
        ("ç", "c"),
        ("Ğ", "G"),
        ("Ü", "U"),
        ("Ş", "S"),
        ("İ", "I"),
        ("Ö", "O"),
        ("Ç", "C"),
    )
