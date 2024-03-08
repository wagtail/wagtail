from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        "{{last_name}} {{company_suffix}}",
        "{{last_name}} & {{last_name}} {{company_suffix}}",
        "{{last_name}} & Søn {{company_suffix}}",
    )

    company_suffixes = (
        "A/S",
        "ApS",
    )
