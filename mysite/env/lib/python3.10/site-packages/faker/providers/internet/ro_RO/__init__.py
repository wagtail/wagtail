from .. import Provider as InternetProvider


class Provider(InternetProvider):
    user_name_formats = (
        "{{last_name_female}}.{{first_name_female}}",
        "{{last_name_female}}.{{first_name_female}}",
        "{{last_name_male}}.{{first_name_male}}",
        "{{last_name_male}}.{{first_name_male}}",
        "{{first_name_female}}.{{last_name_female}}",
        "{{first_name_male}}.{{last_name_male}}",
        "{{first_name}}##",
        "?{{last_name}}",
        "?{{last_name}}",
        "?{{last_name}}",
    )

    email_formats = ("{{user_name}}@{{free_email_domain}}",)

    free_email_domains = (
        "email.ro",
        "gmail.com",
        "kappa.ro",
        "acasa.ro",
        "zzup.ro",
        "141.ro",
        "post.ro",
    )

    tlds = ("ro", "com", "ro")
