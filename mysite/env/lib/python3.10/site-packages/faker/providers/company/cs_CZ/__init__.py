from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        "{{last_name}} {{company_suffix}}",
        "{{last_name}} {{last_name}} {{company_suffix}}",
        "{{last_name}}",
    )

    # Company suffixes are from
    # https://cs.wikipedia.org/wiki/Obchodn%C3%AD_spole%C4%8Dnost
    company_suffixes = (
        "s.r.o.",
        "o.s.",
        "a.s.",
        "v.o.s.",
        "k.s.",
    )
