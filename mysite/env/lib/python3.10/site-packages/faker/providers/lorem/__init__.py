from typing import List, Optional, Sequence, cast

from .. import BaseProvider

localized = True

# 'Latin' is the default locale
default_locale = "la"


class Provider(BaseProvider):
    """Implement default lorem provider for Faker.

    .. important::
       The default locale of the lorem provider is ``la``. When using a locale
       without a localized lorem provider, the ``la`` lorem provider will be
       used, so generated words will be in pseudo-Latin. The locale used for
       the standard provider docs was ``en_US``, and ``en_US`` has a localized
       lorem provider which is why the samples here show words in American
       English.
    """

    word_connector = " "
    sentence_punctuation = "."

    def words(
        self,
        nb: int = 3,
        part_of_speech: Optional[str] = None,
        ext_word_list: Optional[Sequence[str]] = None,
        unique: bool = False,
    ) -> List[str]:
        """Generate a tuple of words.

        The ``nb`` argument controls the number of words in the resulting list,
        and if ``ext_word_list`` is provided, words from that list will be used
        instead of those from the locale provider's built-in word list.

        If ``unique`` is ``True``, this method will return a list containing
        unique words. Under the hood, |random_sample| will be used for sampling
        without replacement. If ``unique`` is ``False``, |random_choices| is
        used instead, and the list returned may contain duplicates.

        ``part_of_speech`` is a parameter that defines to what part of speech
        the returned word belongs. If ``ext_word_list`` is not ``None``, then
        ``part_of_speech`` is ignored. If the value of ``part_of_speech`` does
        not correspond to an existent part of speech according to the set locale,
        then an exception is raised.

        .. warning::
           Depending on the length of a locale provider's built-in word list or
           on the length of ``ext_word_list`` if provided, a large ``nb`` can
           exhaust said lists if ``unique`` is ``True``, raising an exception.

        :sample:
        :sample: nb=5
        :sample: nb=5, ext_word_list=['abc', 'def', 'ghi', 'jkl']
        :sample: nb=4, ext_word_list=['abc', 'def', 'ghi', 'jkl'], unique=True
        """
        if ext_word_list is not None:
            word_list = ext_word_list
        elif part_of_speech:
            if part_of_speech not in self.parts_of_speech:  # type: ignore[attr-defined]
                raise ValueError(f"{part_of_speech} is not recognized as a part of speech.")
            else:
                word_list = self.parts_of_speech[part_of_speech]  # type: ignore[attr-defined]
        else:
            word_list = self.word_list  # type: ignore[attr-defined]

        if unique:
            unique_samples = cast(List[str], self.random_sample(word_list, length=nb))
            return unique_samples
        samples = cast(List[str], self.random_choices(word_list, length=nb))
        return samples

    def word(self, part_of_speech: Optional[str] = None, ext_word_list: Optional[Sequence[str]] = None) -> str:
        """Generate a word.

        This method uses |words| under the hood with the ``nb`` argument set to
        ``1`` to generate the result.

        :sample:
        :sample: ext_word_list=['abc', 'def', 'ghi', 'jkl']
        """
        return self.words(1, part_of_speech, ext_word_list)[0]

    def sentence(
        self, nb_words: int = 6, variable_nb_words: bool = True, ext_word_list: Optional[Sequence[str]] = None
    ) -> str:
        """Generate a sentence.

        The ``nb_words`` argument controls how many words the sentence will
        contain, and setting ``variable_nb_words`` to ``False`` will generate
        the exact amount, while setting it to ``True`` (default) will generate
        a random amount (+/-40%, minimum of 1) using |randomize_nb_elements|.

        Under the hood, |words| is used to generate the words, so the argument
        ``ext_word_list`` works in the same way here as it would in that method.

        :sample: nb_words=10
        :sample: nb_words=10, variable_nb_words=False
        :sample: nb_words=10, ext_word_list=['abc', 'def', 'ghi', 'jkl']
        :sample: nb_words=10, variable_nb_words=True,
                 ext_word_list=['abc', 'def', 'ghi', 'jkl']
        """
        if nb_words <= 0:
            return ""

        if variable_nb_words:
            nb_words = self.randomize_nb_elements(nb_words, min=1)

        words = list(self.words(nb=nb_words, ext_word_list=ext_word_list))
        words[0] = words[0].title()

        return self.word_connector.join(words) + self.sentence_punctuation

    def sentences(self, nb: int = 3, ext_word_list: Optional[Sequence[str]] = None) -> List[str]:
        """Generate a list of sentences.

        This method uses |sentence| under the hood to generate sentences, and
        the ``nb`` argument controls exactly how many sentences the list will
        contain. The ``ext_word_list`` argument works in exactly the same way
        as well.

        :sample:
        :sample: nb=5
        :sample: nb=5, ext_word_list=['abc', 'def', 'ghi', 'jkl']
        """
        return [self.sentence(ext_word_list=ext_word_list) for _ in range(0, nb)]

    def paragraph(
        self, nb_sentences: int = 3, variable_nb_sentences: bool = True, ext_word_list: Optional[Sequence[str]] = None
    ) -> str:
        """Generate a paragraph.

        The ``nb_sentences`` argument controls how many sentences the paragraph
        will contain, and setting ``variable_nb_sentences`` to ``False`` will
        generate the exact amount, while setting it to ``True`` (default) will
        generate a random amount (+/-40%, minimum of 1) using
        |randomize_nb_elements|.

        Under the hood, |sentences| is used to generate the sentences, so the
        argument ``ext_word_list`` works in the same way here as it would in
        that method.

        :sample: nb_sentences=5
        :sample: nb_sentences=5, variable_nb_sentences=False
        :sample: nb_sentences=5, ext_word_list=['abc', 'def', 'ghi', 'jkl']
        :sample: nb_sentences=5, variable_nb_sentences=False,
                 ext_word_list=['abc', 'def', 'ghi', 'jkl']
        """
        if nb_sentences <= 0:
            return ""

        if variable_nb_sentences:
            nb_sentences = self.randomize_nb_elements(nb_sentences, min=1)

        para = self.word_connector.join(self.sentences(nb_sentences, ext_word_list=ext_word_list))

        return para

    def paragraphs(self, nb: int = 3, ext_word_list: Optional[Sequence[str]] = None) -> List[str]:
        """Generate a list of paragraphs.

        This method uses |paragraph| under the hood to generate paragraphs, and
        the ``nb`` argument controls exactly how many sentences the list will
        contain. The ``ext_word_list`` argument works in exactly the same way
        as well.

        :sample: nb=5
        :sample: nb=5, ext_word_list=['abc', 'def', 'ghi', 'jkl']
        """
        return [self.paragraph(ext_word_list=ext_word_list) for _ in range(0, nb)]

    def text(self, max_nb_chars: int = 200, ext_word_list: Optional[Sequence[str]] = None) -> str:
        """Generate a text string.

        The ``max_nb_chars`` argument controls the approximate number of
        characters the text string will have, and depending on its value, this
        method may use either |words|, |sentences|, or |paragraphs| for text
        generation. The ``ext_word_list`` argument works in exactly the same way
        it would in any of those methods.

        :sample: max_nb_chars=20
        :sample: max_nb_chars=80
        :sample: max_nb_chars=160
        :sample: ext_word_list=['abc', 'def', 'ghi', 'jkl']
        """
        text: List[str] = []
        if max_nb_chars < 5:
            raise ValueError("text() can only generate text of at least 5 characters")

        if max_nb_chars < 25:
            # join words
            while not text:
                size = 0
                # determine how many words are needed to reach the $max_nb_chars
                # once;
                while size < max_nb_chars:
                    word = (self.word_connector if size else "") + self.word(ext_word_list=ext_word_list)
                    text.append(word)
                    size += len(word)
                text.pop()
            text[0] = text[0][0].upper() + text[0][1:]
            last_index = len(text) - 1
            text[last_index] += self.sentence_punctuation
        elif max_nb_chars < 100:
            # join sentences
            while not text:
                size = 0
                # determine how many sentences are needed to reach the
                # $max_nb_chars once
                while size < max_nb_chars:
                    sentence = (self.word_connector if size else "") + self.sentence(ext_word_list=ext_word_list)
                    text.append(sentence)
                    size += len(sentence)
                text.pop()
        else:
            # join paragraphs
            while not text:
                size = 0
                # determine how many paragraphs are needed to reach the
                # $max_nb_chars once
                while size < max_nb_chars:
                    paragraph = ("\n" if size else "") + self.paragraph(ext_word_list=ext_word_list)
                    text.append(paragraph)
                    size += len(paragraph)
                text.pop()

        return "".join(text)

    def texts(
        self, nb_texts: int = 3, max_nb_chars: int = 200, ext_word_list: Optional[Sequence[str]] = None
    ) -> List[str]:
        """Generate a list of text strings.

        The ``nb_texts`` argument controls how many text strings the list will
        contain, and this method uses |text| under the hood for text generation,
        so the two remaining arguments, ``max_nb_chars`` and ``ext_word_list``
        will work in exactly the same way as well.

        :sample: nb_texts=5
        :sample: nb_texts=5, max_nb_chars=50
        :sample: nb_texts=5, max_nb_chars=50,
                 ext_word_list=['abc', 'def', 'ghi', 'jkl']
        """
        return [self.text(max_nb_chars, ext_word_list) for _ in range(0, nb_texts)]
