from collections import OrderedDict

from faker.utils.decorators import lowercase, slugify

from .. import Provider as InternetProvider


class Provider(InternetProvider):
    """
    Provider for internet stuff for en_PH locale

    Free email domains are based on anecdotal evidence and experience. Available TLDs are based on the listed sources.
    Because of the local company naming scheme, a custom generator is needed to output convincing company domains.

    Sources:
    - https://en.wikipedia.org/wiki/.ph
    """

    tlds = (
        "com",
        "net",
        "org",
        "ph",
        "com.ph",
        "net.ph",
        "org.ph",
    )
    safe_email_tlds = tlds
    free_email_domains = (
        "gmail.com",
        "yahoo.com",
        "zohomail.com",
    )
    email_formats = OrderedDict(
        [
            ("{{user_name}}@{{domain_name}}", 0.75),
            ("{{user_name}}@{{free_email_domain}}", 0.25),
        ]
    )

    @lowercase
    @slugify
    def domain_word(self) -> str:
        check = self.random_int(0, 99)
        if check % 100 < 40:
            company_acronym = self.generator.format("random_company_acronym")
            if len(company_acronym) == 2:
                company_type = self.generator.format("company_type")
                return company_acronym + company_type
            else:
                return company_acronym
        else:
            if check % 2 == 0:
                name_part = self.generator.format("last_name")
            else:
                name_part = self.generator.format("random_company_adjective")
            company_noun_chain = self.generator.format("random_company_noun_chain")
            company_nouns = company_noun_chain.split(" ")
            if len(company_nouns) == 1:
                return name_part + company_noun_chain
            else:
                company_type = self.generator.format("company_type")
                company_elements = [name_part] + company_nouns
                acronym = "".join([word[0] for word in company_elements])
                return acronym + company_type
