from .codes import codes


def unidecode(txt: str) -> str:
    chars = ""
    for ch in txt:
        codepoint = ord(ch)

        try:
            chars += codes[codepoint]
        except IndexError:
            pass
    return chars
