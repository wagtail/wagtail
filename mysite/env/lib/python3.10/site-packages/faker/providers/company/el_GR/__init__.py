from .. import Provider as CompanyProvider


class Provider(CompanyProvider):
    formats = (
        "{{last_name}} {{company_suffix}}",
        "{{last_name}}-{{last_name}}",
        "{{last_name}}-{{last_name}} {{company_suffix}}",
        "{{last_name}}, {{last_name}} και {{last_name}}",
    )
    company_suffixes = ("Α.Ε.", "και υιοί", "Ο.Ε.", "Α.Β.Ε.Ε.", "Α.Ε. ΟΜΙΛΟΣ ΕΤΑΙΡΕΙΩΝ")
