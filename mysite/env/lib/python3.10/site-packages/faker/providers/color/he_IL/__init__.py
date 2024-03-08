from collections import OrderedDict

from .. import Provider as ColorProvider

localized = True


class Provider(ColorProvider):
    """Implement color provider for ``he_IL`` locale."""

    """Source : https://he.wikipedia.org/wiki/%D7%95%D7%99%D7%A7%D7%99%D7%A4%D7%93%D7%99%D7%94:%D7%A2%D7%A8%D7%9B%D7%AA_%D7%A6%D7%91%D7%A2%D7%99%D7%9D#%D7%98%D7%91%D7%9C%D7%94_%D7%96%D7%95_%D7%9E%D7%A8%D7%90%D7%94_%D7%90%D7%AA_%D7%98%D7%95%D7%95%D7%97_%D7%94%D7%92%D7%95%D7%95%D7%A0%D7%99%D7%9D_%D7%A9%D7%9C_%D7%9B%D7%9E%D7%94_%D7%A6%D7%91%D7%A2%D7%99%D7%9D_%D7%A0%D7%A4%D7%95%D7%A6%D7%99%D7%9D"""  # NOQA

    all_colors = OrderedDict(
        (
            ("אדום", "#FF0000"),
            ("אוכרה", "#DDAA33"),
            ("אינדיגו", "#4B0082"),
            ("אפור", "#7F7F7F"),
            ("ארגמן", "#7F003F"),
            ("ורוד", "#FF007F"),
            ("זהב", "#FFDF00"),
            ("חאקי", "#C3B091"),
            ("חום", "#7F3F00"),
            ("טורקיז", "#40E0D0"),
            ("ירוק", "#00FF00"),
            ("כחול", "#0000FF"),
            ("כסף", "#C0C0C0"),
            ("כתום", "#FF7F00"),
            ("לבן", "#FFFFFF"),
            ("מג'נטה", "#FF00FF"),
            ("סגול", "#7F00FF"),
            ("צהוב", "#FFFF00"),
            ("ציאן", "#00FFFF"),
            ("קרדינל", "#C41E3A"),
            ("שחור", "#000000"),
            ("שני", "#7F0000"),
            ("תכלת", "#007FFF"),
        )
    )

    safe_colors = (
        "אדום",
        "ירוק",
        "כחול",
        "צהוב",
        "ציאן",
        "מג'נטה",
        "לבן",
    )
