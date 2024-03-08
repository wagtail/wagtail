from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        "{{last_name}} {{company_suffix}}",
        "{{last_name}}-{{last_name}} {{company_suffix}}",
        "{{last_name}}, {{last_name}} en {{last_name}} {{company_suffix}}",
    )
    company_suffixes = ("NV", "BV", "CV", "VOF", "CommV")
