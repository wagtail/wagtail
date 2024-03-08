from .. import Provider as InternetProvider


class Provider(InternetProvider):
    """
    Implement internet provider for ``bn_BD`` locale.
    """

    free_email_domains = (
        "gmail.com",
        "yahoo.com",
        "hotmail.com",
        "mail.ru",
        "yandex.ru",
        "rambler.ru",
    )

    tlds = (
        "com",
        "com",
        "com",
        "com",
        "com",
        "com",
        "biz",
        "info",
        "net",
        "org",
        "com.bd",
    )
