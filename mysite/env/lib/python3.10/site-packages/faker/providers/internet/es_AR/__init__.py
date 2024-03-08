from .. import Provider as InternetProvider


class Provider(InternetProvider):
    safe_email_tlds = ("com", "net", "ar")
    tlds = ("com", "com.ar", "com.ar", "net", "org", "net.ar", "ar", "ar")
    replacements = (
        ("à", "a"),
        ("â", "a"),
        ("ã", "a"),
        ("á", "a"),
        ("ç", "c"),
        ("é", "e"),
        ("ê", "e"),
        ("í", "i"),
        ("ô", "o"),
        ("ö", "o"),
        ("õ", "o"),
        ("ó", "o"),
        ("ú", "u"),
    )
