from typing import List

from faker.utils.decorators import lowercase, slugify_unicode

from .. import Provider as InternetProvider


class Provider(InternetProvider):
    safe_email_tlds = ("com", "net", "cl", "cl")
    tlds = ("com", "com", "com", "net", "org", "cl", "cl", "cl")
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

    @lowercase
    @slugify_unicode
    def domain_word(self) -> str:
        company: str = self.generator.format("company")
        company_elements: List[str] = company.split(" ")
        # select 2 items as companies include prefix
        name_items = company_elements[:2]
        return self._to_ascii("".join(name_items))
