from .. import Provider as InternetProvider


class Provider(InternetProvider):
    free_email_domains = (
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "yahoo.com.au",
        "hotmail.com.au",
    )

    tlds = (
        "com",
        "com.au",
        "org",
        "org.au",
        "net",
        "net.au",
        "biz",
        "info",
        "edu",
        "edu.au",
    )
