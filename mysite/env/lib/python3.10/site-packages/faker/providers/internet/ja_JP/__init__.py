from faker.utils.decorators import slugify

from .. import Provider as InternetProvider


class Provider(InternetProvider):
    user_name_formats = (
        "{{last_romanized_name}}.{{first_romanized_name}}",
        "{{first_romanized_name}}.{{last_romanized_name}}",
        "{{first_romanized_name}}##",
        "?{{last_romanized_name}}",
    )
    tlds = ("com", "com", "com", "net", "org", "jp", "jp", "jp")

    @slugify
    def domain_word(self) -> str:
        return self.generator.format("last_romanized_name")
