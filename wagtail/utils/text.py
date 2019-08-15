from unidecode import unidecode


def string_to_ascii(value) -> str:
    return str(unidecode(value))
