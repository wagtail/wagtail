from faker.utils.datasets import add_ordereddicts

from .. import BaseProvider, ElementsType

localized = True


class Provider(BaseProvider):
    formats: ElementsType[str] = ["{{first_name}} {{last_name}}"]

    first_names: ElementsType[str] = ["John", "Jane"]

    last_names: ElementsType[str] = ["Doe"]

    # https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes
    language_names: ElementsType[str] = [
        "Afar",
        "Abkhazian",
        "Avestan",
        "Afrikaans",
        "Akan",
        "Amharic",
        "Aragonese",
        "Arabic",
        "Assamese",
        "Avaric",
        "Aymara",
        "Azerbaijani",
        "Bashkir",
        "Belarusian",
        "Bulgarian",
        "Bihari languages",
        "Bislama",
        "Bambara",
        "Bengali",
        "Tibetan",
        "Breton",
        "Bosnian",
        "Catalan",
        "Chechen",
        "Chamorro",
        "Corsican",
        "Cree",
        "Czech",
        "Church Slavic",
        "Chuvash",
        "Welsh",
        "Danish",
        "German",
        "Divehi",
        "Dzongkha",
        "Ewe",
        "Greek",
        "English",
        "Esperanto",
        "Spanish",
        "Estonian",
        "Basque",
        "Persian",
        "Fulah",
        "Finnish",
        "Fijian",
        "Faroese",
        "French",
        "Western Frisian",
        "Irish",
        "Gaelic",
        "Galician",
        "Guarani",
        "Gujarati",
        "Manx",
        "Hausa",
        "Hebrew",
        "Hindi",
        "Hiri Motu",
        "Croatian",
        "Haitian",
        "Hungarian",
        "Armenian",
        "Herero",
        "Interlingua",
        "Indonesian",
        "Interlingue",
        "Igbo",
        "Sichuan Yi",
        "Inupiaq",
        "Ido",
        "Icelandic",
        "Italian",
        "Inuktitut",
        "Japanese",
        "Javanese",
        "Georgian",
        "Kongo",
        "Kikuyu",
        "Kuanyama",
        "Kazakh",
        "Kalaallisut",
        "Central Khmer",
        "Kannada",
        "Korean",
        "Kanuri",
        "Kashmiri",
        "Kurdish",
        "Komi",
        "Cornish",
        "Kirghiz",
        "Latin",
        "Luxembourgish",
        "Ganda",
        "Limburgan",
        "Lingala",
        "Lao",
        "Lithuanian",
        "Luba-Katanga",
        "Latvian",
        "Malagasy",
        "Marshallese",
        "Maori",
        "Macedonian",
        "Malayalam",
        "Mongolian",
        "Marathi",
        "Malay",
        "Maltese",
        "Burmese",
        "Nauru",
        "North Ndebele",
        "Nepali",
        "Ndonga",
        "Dutch",
        "Norwegian Nynorsk",
        "Norwegian",
        "South Ndebele",
        "Navajo",
        "Chichewa",
        "Occitan",
        "Ojibwa",
        "Oromo",
        "Oriya",
        "Ossetian",
        "Panjabi",
        "Pali",
        "Polish",
        "Pushto",
        "Portuguese",
        "Quechua",
        "Romansh",
        "Rundi",
        "Romanian",
        "Russian",
        "Kinyarwanda",
        "Sanskrit",
        "Sardinian",
        "Sindhi",
        "Northern Sami",
        "Sango",
        "Sinhala",
        "Slovak",
        "Slovenian",
        "Samoan",
        "Shona",
        "Somali",
        "Albanian",
        "Serbian",
        "Swati",
        "Sotho, Southern",
        "Sundanese",
        "Swedish",
        "Swahili",
        "Tamil",
        "Telugu",
        "Tajik",
        "Thai",
        "Tigrinya",
        "Turkmen",
        "Tagalog",
        "Tswana",
        "Tonga",
        "Turkish",
        "Tsonga",
        "Tatar",
        "Twi",
        "Tahitian",
        "Uighur",
        "Ukrainian",
        "Urdu",
        "Uzbek",
        "Venda",
        "Vietnamese",
        "Walloon",
        "Wolof",
        "Xhosa",
        "Yiddish",
        "Yoruba",
        "Zhuang",
        "Chinese",
        "Zulu",
    ]

    def name(self) -> str:
        """
        :example: 'John Doe'
        """
        pattern: str = self.random_element(self.formats)
        return self.generator.parse(pattern)

    def first_name(self) -> str:
        return self.random_element(self.first_names)

    def last_name(self) -> str:
        return self.random_element(self.last_names)

    def name_male(self) -> str:
        if hasattr(self, "formats_male"):
            formats = self.formats_male  # type: ignore[attr-defined]
        else:
            formats = self.formats
        pattern: str = self.random_element(formats)
        return self.generator.parse(pattern)

    def name_nonbinary(self) -> str:
        if hasattr(self, "formats_nonbinary"):
            formats = self.formats_nonbinary  # type: ignore[attr-defined]
        else:
            formats = self.formats
        pattern: str = self.random_element(formats)
        return self.generator.parse(pattern)

    def name_female(self) -> str:
        if hasattr(self, "formats_female"):
            formats = self.formats_female  # type: ignore[attr-defined]
        else:
            formats = self.formats
        pattern: str = self.random_element(formats)
        return self.generator.parse(pattern)

    def first_name_male(self) -> str:
        if hasattr(self, "first_names_male"):
            return self.random_element(self.first_names_male)  # type: ignore[attr-defined]
        return self.first_name()

    def first_name_nonbinary(self) -> str:
        if hasattr(self, "first_names_nonbinary"):
            return self.random_element(self.first_names_nonbinary)  # type: ignore[attr-defined]
        return self.first_name()

    def first_name_female(self) -> str:
        if hasattr(self, "first_names_female"):
            return self.random_element(self.first_names_female)  # type: ignore[attr-defined]
        return self.first_name()

    def last_name_male(self) -> str:
        if hasattr(self, "last_names_male"):
            return self.random_element(self.last_names_male)  # type: ignore[attr-defined]
        return self.last_name()

    def last_name_nonbinary(self) -> str:
        if hasattr(self, "last_names_nonbinary"):
            return self.random_element(self.last_names_nonbinary)  # type: ignore[attr-defined]
        return self.last_name()

    def last_name_female(self) -> str:
        if hasattr(self, "last_names_female"):
            return self.random_element(self.last_names_female)  # type: ignore[attr-defined]
        return self.last_name()

    def prefix(self) -> str:
        if hasattr(self, "prefixes"):
            return self.random_element(self.prefixes)  # type: ignore[attr-defined]
        if hasattr(self, "prefixes_male") and hasattr(self, "prefixes_female") and hasattr(self, "prefixes_nonbinary"):
            prefixes = add_ordereddicts(
                self.prefixes_male,  # type: ignore[attr-defined]
                self.prefixes_female,  # type: ignore[attr-defined]
                self.prefixes_nonbinary,  # type: ignore[attr-defined]
            )
            return self.random_element(prefixes)
        if hasattr(self, "prefixes_male") and hasattr(self, "prefixes_female"):
            prefixes = self.random_element((self.prefixes_male, self.prefixes_female))  # type: ignore[attr-defined]
            return self.random_element(prefixes)
        return ""

    def prefix_male(self) -> str:
        if hasattr(self, "prefixes_male"):
            return self.random_element(self.prefixes_male)  # type: ignore[attr-defined]
        return self.prefix()

    def prefix_nonbinary(self) -> str:
        if hasattr(self, "prefixes_nonbinary"):
            return self.random_element(self.prefixes_nonbinary)  # type: ignore[attr-defined]
        return self.prefix()

    def prefix_female(self) -> str:
        if hasattr(self, "prefixes_female"):
            return self.random_element(self.prefixes_female)  # type: ignore[attr-defined]
        return self.prefix()

    def suffix(self) -> str:
        if hasattr(self, "suffixes"):
            return self.random_element(self.suffixes)  # type: ignore[attr-defined]
        if hasattr(self, "suffixes_male") and hasattr(self, "suffixes_female") and hasattr(self, "suffixes_nonbinary"):
            suffixes = add_ordereddicts(
                self.suffixes_male,  # type: ignore[attr-defined]
                self.suffixes_female,  # type: ignore[attr-defined]
                self.suffixes_nonbinary,  # type: ignore[attr-defined]
            )
            return self.random_element(suffixes)
        if hasattr(self, "suffixes_male") and hasattr(self, "suffixes_female"):
            suffixes = self.random_element((self.suffixes_male, self.suffixes_female))  # type: ignore[attr-defined]
            return self.random_element(suffixes)
        return ""

    def suffix_male(self) -> str:
        if hasattr(self, "suffixes_male"):
            return self.random_element(self.suffixes_male)  # type: ignore[attr-defined]
        return self.suffix()

    def suffix_nonbinary(self) -> str:
        if hasattr(self, "suffixes_nonbinary"):
            return self.random_element(self.suffixes_nonbinary)  # type: ignore[attr-defined]
        return self.suffix()

    def suffix_female(self) -> str:
        if hasattr(self, "suffixes_female"):
            return self.random_element(self.suffixes_female)  # type: ignore[attr-defined]
        return self.suffix()

    def language_name(self) -> str:
        """Generate a random i18n language name (e.g. English)."""
        return self.random_element(self.language_names)
