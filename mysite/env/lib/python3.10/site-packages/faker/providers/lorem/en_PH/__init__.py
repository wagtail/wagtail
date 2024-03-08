from typing import List

from ..en_US import Provider as EnUsProvider
from ..la import Provider as LoremProvider


class Provider(LoremProvider):
    """Implement lorem provider for ``en_PH`` locale.

    This localized provider generates pseudo-Latin text when using the standard
    lorem provider methods, and the ``english_*`` methods are also provided for
    generating text in American English. Both languages are used in this locale
    for this purpose.

    All the ``english_*`` methods use their corresponding standard lorem
    provider method under the hood with ``ext_word_list`` set to the
    |EnUsLoremProvider|'s word list.

    .. |EnUsLoremProvider| replace::
        :meth:`EnUsLoremProvider <faker.providers.lorem.en_US.Provider>`
    """

    english_word_list = EnUsProvider.word_list

    def english_word(self) -> str:
        """Generate an English word."""
        return self.word(ext_word_list=self.english_word_list)

    def english_words(self, nb: int = 3, unique: bool = False) -> List[str]:
        """Generate a list of English words.

        :sample: nb=5
        :sample: nb=5, unique=True
        """
        return self.words(nb=nb, ext_word_list=self.english_word_list, unique=unique)

    def english_sentence(self, nb_words: int = 6, variable_nb_words: bool = True) -> str:
        """Generate a sentence in English.

        :sample: nb_words=10
        :sample: nb_words=10, variable_nb_words=False
        """
        return self.sentence(nb_words, variable_nb_words, self.english_word_list)

    def english_sentences(self, nb: int = 3) -> List[str]:
        """Generate a list of sentences in English.

        :sample: nb=5
        """
        return self.sentences(nb, self.english_word_list)

    def english_paragraph(self, nb_sentences: int = 3, variable_nb_sentences: bool = True) -> str:
        """Generate a paragraph in English.

        :sample: nb_sentences=5
        :sample: nb_sentences=5, variable_nb_sentences=False
        """
        return self.paragraph(nb_sentences, variable_nb_sentences, self.english_word_list)

    def english_paragraphs(self, nb: int = 3) -> List[str]:
        """Generate a list of paragraphs in English.

        :sample: nb=5
        """
        return self.paragraphs(nb, self.english_word_list)

    def english_text(self, max_nb_chars: int = 200) -> str:
        """Generate a text string in English.

        :sample: max_nb_chars=20
        :sample: max_nb_chars=80
        :sample: max_nb_chars=160
        """
        return self.text(max_nb_chars, self.english_word_list)

    def english_texts(self, nb_texts: int = 3, max_nb_chars: int = 200) -> List[str]:
        """Generate a list of text strings in English.

        :sample: nb_texts=5
        :sample: nb_texts=5, max_nb_chars=50
        """
        return self.texts(nb_texts, max_nb_chars, self.english_word_list)
