from .. import Provider as BaseProvider


class Provider(BaseProvider):
    safe_email_tlds = ("com", "net", "ir", "org")
    free_email_domains = (
        "chmail.ir",
        "mailfa.com",
        "gmail.com",
        "hotmail.com",
        "yahoo.com",
    )
    tlds = ("com", "com", "com", "net", "org", "ir", "ir", "ir")
