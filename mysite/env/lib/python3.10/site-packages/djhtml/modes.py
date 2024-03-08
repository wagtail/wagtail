import re

from .lines import Line
from .tokens import Token


class BaseMode:
    """
    Base class for the different modes.

    """

    MAX_LINE_LENGTH = 10_000

    def __init__(self, source=None, return_mode=None):
        """
        Instantiate with source text before calling indent(), or
        with the return_mode when invoked from within another mode.

        """
        assert type(self) is not BaseMode
        assert source is not None or return_mode

        self.source = source
        self.return_mode = return_mode or self
        self.token_re = compile_re(self.RAW_TOKENS)

        # To keep track of the current and previous offsets.
        self.offsets = dict(relative=0, absolute=0)
        self.previous_offsets = []

    def indent(self, tabwidth):
        """
        Return the indented text as a single string.

        """
        self.tokenize()
        self.parse()
        return "\n".join([line.indent(tabwidth) for line in self.lines])

    def tokenize(self):
        """
        Split the source text into tokens and place them on lines.

        How text is split into raw tokens is defined by the regexes
        of each mode. For each raw token, the create_token() method of
        the mode is called.

        Some tokens, such a <style> or <script> tags in HTML, can
        switch to a different mode by returning a new instance of that
        mode alongside the token.

        """
        self.lines = []
        line = Line()
        mode = self
        src = self.source

        while True:
            if src.find("\n") > mode.MAX_LINE_LENGTH:
                raise MaxLineLengthExceeded

            try:
                # Split the source at the first occurrence of one of
                # the current mode's raw tokens.
                head, raw_token, tail = mode.token_re.split(src, maxsplit=1)

            except ValueError:
                # We've reached the final line!
                if src:
                    token, _ = mode.create_token(src, "", line)
                    line.append(token)
                self.lines.append(line)
                break

            if head:
                # Create a token from the head.
                token, mode = mode.create_token(head, raw_token + tail, line)
                line.append(token)

            if raw_token == "\n":
                self.lines.append(line)
                line = Line()

            else:
                # Create a token from the tail
                token, mode = mode.create_token(raw_token, tail, line)
                line.append(token)

            # Set the new source to the old tail for the next iteration.
            src = tail

    def parse(self):
        """
        You found the top-secret indenting algorithm!

        Once the source has been split into tokens, the indentation is
        solely determined by the attributes of the tokens. This makes
        the algorithm independent of the language (HTML, CSS, JS), and
        thereby accomodates different languages used interchangeably.

        """
        stack = []

        def mode_in_stack(mode):
            """
            Helper function to see if a token from a specific mode
            is in the stack.

            """
            if stack[-1].mode is DjTXT:
                # See paradoxes.html and issue #17
                return False
            for token in stack:
                if token.mode is mode:
                    return True
            return False

        for line in self.lines:
            first_token = True
            for token in line.tokens:
                opening_token = None
                if stack:
                    # When a dedenting token is found, pop the
                    # corresponding opening token from the stack.
                    if token.dedents:
                        if stack[-1].mode is token.mode:
                            opening_token = stack.pop()
                            if stack and (opening_token.is_double or token.is_double):
                                opening_token = stack.pop()

                        # Error: the opening token is from a different
                        # mode. Pop the stack until the correct
                        # opening token is found.
                        elif mode_in_stack(token.mode):
                            opening_token = stack.pop()
                            while opening_token.mode is not token.mode:
                                opening_token = stack.pop()

                        # Error: there are no tokens in the stack of
                        # the same mode. Set the line level to a sane
                        # value.
                        elif first_token:
                            line.level = stack[-1].level + 1

                        # Success! If the dedenting token is first in
                        # line, set the line level to the level of the
                        # opening token.
                        if first_token and opening_token:
                            line.level = opening_token.level

                    # For non-dedenting tokens, set the line one level
                    # higher than the opening token's level.
                    else:
                        if token.is_double and stack[-1].is_double:
                            opening_token = stack.pop()
                        if stack and first_token:
                            line.level = stack[-1].level + 1

                # Adjust line level according to the token's offsets.
                if first_token:
                    line.level = line.level + token.relative
                    line.offset = token.absolute
                    line.ignore = token.ignore

                # Push indenting tokens onto the stack.
                if token.indents:
                    token.level = opening_token.level if opening_token else line.level
                    stack.append(token)

                if token.text.strip():
                    first_token = False

    def debug(self):
        self.tokenize()
        self.parse()
        return "\n".join([repr(line) for line in self.lines])


class DjTXT(BaseMode):
    """
    Mode for indenting text containing Django/Jinja template tags.

    This mode is special because all the other modes inherit from it,
    because all other modes can contain Django/Jinja template tags.

    """

    RAW_TOKENS = [
        r"\n",
        r"{%[-+]?.*?[-+]?%}",
        r"{#",
        r"{{.*?}}",
    ]
    CLOSING_AND_OPENING_TAGS = [
        "elif",
        "else",
        "empty",
        "plural",
    ]
    COMMENT_TAGS = [
        "comment",
        "verbatim",
        "raw",
    ]
    AMBIGUOUS_BLOCK_TAGS = {
        # token_name: (regex_if_block, regex_if_not_block)
        "set": (None, " = "),
        "video": (" as ", None),
        "placeholder": (" or ", None),
    }
    OPENING_TAG = r"{%[-+]? *[#/]?(\w+).*?[-+]?%}"

    def create_token(self, raw_token, src, line):
        mode = self

        if tag := re.match(self.OPENING_TAG, raw_token):
            name = tag.group(1)
            if name in self.COMMENT_TAGS:
                token, mode = Token.Open(raw_token, mode=DjTXT, ignore=True), Comment(
                    "{% *end" + name + " *%}", mode=DjTXT, return_mode=self
                )
            elif name.startswith("end") or re.match(r"{% */\w+", raw_token):
                token = Token.Close(raw_token, mode=DjTXT, **self.offsets)
            elif self._has_closing_token(name, raw_token, src):
                token = Token.Open(raw_token, mode=DjTXT, **self.offsets)
            elif name in self.CLOSING_AND_OPENING_TAGS:
                token = Token.CloseAndOpen(raw_token, mode=DjTXT, **self.offsets)
            else:
                token = Token.Text(raw_token, mode=DjTXT, **self.offsets)
        elif raw_token == "{#":
            token, mode = Token.Open(raw_token, mode=DjTXT, ignore=True), Comment(
                "{# fmt:on #}", mode=DjTXT, return_mode=self
            ) if src.startswith(" fmt:off #}") else Comment(
                "#}", mode=DjTXT, return_mode=self
            )

        else:
            token = Token.Text(raw_token, mode=self.__class__, **self.offsets)

        return token, mode

    def _has_closing_token(self, name, raw_token, src):
        if not re.search(f"{{%[-+]? *(end|/){name}(?: .*?|)%}}", src):
            return False
        if regex := self.AMBIGUOUS_BLOCK_TAGS.get(name):
            if regex[0]:
                return re.search(regex[0], raw_token)
            if regex[1]:
                return not re.search(regex[1], raw_token)
        return True


class DjHTML(DjTXT):
    """
    Mode for indenting HTML.

    """

    RAW_TOKENS = DjTXT.RAW_TOKENS + [
        r"<pre.*?>",
        r"</.*?>",
        r"<!--",
        r"<",
    ]

    IGNORE_TAGS = [
        "area",
        "base",
        "br",
        "col",
        "command",
        "embed",
        "hr",
        "img",
        "input",
        "keygen",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    ]

    def create_token(self, raw_token, src, line):
        mode = self

        if raw_token == "<":
            if match := re.match(r"([\w\-\.:]+)(\s*)", src):
                tagname = match[1]
                following_spaces = match[2]
                absolute = True
                token = Token.Text(raw_token, mode=DjHTML)
                offsets = dict(
                    relative=-1 if line.indents else 0,
                    absolute=len(line) + len(tagname) + 2,
                )
                if "\n" in following_spaces:
                    # Use "relative" multi-line indendation instead
                    absolute = False
                    token.indents = True
                    offsets = dict(relative=0, absolute=0)
                mode = InsideHTMLTag(tagname, line, self, absolute, offsets)
            else:
                token = Token.Text(raw_token, mode=DjHTML)
        elif raw_token == "<!--":
            token, mode = Token.Open(raw_token, mode=DjHTML, ignore=True), Comment(
                "-->", mode=DjHTML, return_mode=self
            )
        elif re.match("<pre.*?>", raw_token):
            token, mode = Token.Open(raw_token, mode=DjHTML, ignore=True), Comment(
                "</pre>", mode=DjHTML, return_mode=self
            )
        elif raw_token.startswith("</"):
            token = Token.Close(raw_token, mode=DjHTML)
            if tagname := re.search(r"\w+", raw_token):
                if tagname[0].lower() in self.IGNORE_TAGS:
                    token = Token.Text(raw_token, mode=DjHTML)
        else:
            token, mode = super().create_token(raw_token, src, line)

        return token, mode


class DjCSS(DjTXT):
    """
    Mode for indenting CSS.

    """

    RAW_TOKENS = DjTXT.RAW_TOKENS + [
        r"://",
        r"//.*",
        r"[{()}]",
        r"/\*",
        r'"(?:\\.|[^\\"])*"',  # "string"
        r"'(?:\\.|[^\\'])*'",  # 'string'
        r"[\w-]+: ",
        r";",
        r"</style>",
    ]

    def create_token(self, raw_token, src, line):
        mode = self

        if raw_token in "{(":
            self.previous_offsets.append(self.offsets.copy())
            self.offsets = dict(relative=0, absolute=0)
            token = Token.Open(raw_token, mode=DjCSS)
        elif raw_token in "})":
            if self.previous_offsets:
                self.offsets = self.previous_offsets.pop()
            token = Token.Close(raw_token, mode=DjCSS)
        elif raw_token.endswith(": "):
            token = Token.Text(raw_token, mode=DjCSS, **self.offsets)
            self.offsets["absolute"] = len(line) + len(raw_token)
        elif raw_token == ";":
            self.offsets["absolute"] = 0
            token = Token.Text(raw_token, mode=DjCSS, **self.offsets)
        elif raw_token == "/*":
            token, mode = Token.Open(raw_token, mode=DjCSS, ignore=True), Comment(
                r"\*/", mode=DjCSS, return_mode=self
            )
        elif raw_token.startswith("//"):
            token = Token.Text(raw_token, mode=DjCSS, ignore=True)
        elif raw_token == "</style>":
            token, mode = (
                Token.Close(raw_token, mode=self.return_mode.__class__),
                self.return_mode,
            )
        else:
            token, mode = super().create_token(raw_token, src, line)

        return token, mode


class DjJS(DjTXT):
    """
    Mode for indenting Javascript.

    """

    RAW_TOKENS = DjTXT.RAW_TOKENS + [
        r"//.*",
        r"/\*",
        r"[$\w-]+:",
        r'"(?:\\.|[^"])*"',  # "string"
        r"'(?:\\.|[^'])*'",  # 'string'
        r"`(?:\\.|[^`])*`",  # `string`
        r"/(?=[^ ])(?:\\.|[^/\n])*/",  # /[^ ]string/
        r"[{[()\]}]",
        r"var ",
        r"let ",
        r"const ",
        r"if(?= *\()",
        r"else(?= *\n)",
        r"for(?= *\()",
        r"while(?= *\()",
        r"</script>",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.haskell = False
        self.haskell_re = re.compile(r"^ *, ([$\w-]+ *=|[$\w-]+;?)")
        self.variable_re = re.compile(r"^ *([$\w-]+ *=|[$\w-]+;?)")
        self.previous_line_ended_with_comma = False

    def create_token(self, raw_token, src, line):
        mode = self
        persist_relative_offset = False

        # Reset absolute offset in almost all cases
        if (
            not line
            and not self.haskell_re.match(raw_token)
            and not (
                self.variable_re.match(raw_token)
                and self.previous_line_ended_with_comma
            )
        ):
            self.offsets["absolute"] = 0

        # Opening and closing tokens
        if raw_token in "{[(":
            self.previous_offsets.append(self.offsets.copy())
            self.offsets = dict(relative=0, absolute=0)
            token = Token.Open(raw_token, mode=DjJS)
        elif raw_token in ")]}":
            if self.previous_offsets:
                self.offsets = self.previous_offsets.pop()
            if raw_token == ")":
                persist_relative_offset = True
            token = Token.Close(raw_token, mode=DjJS)
        elif raw_token == "/*":
            token, mode = Token.Open(raw_token, mode=DjJS, ignore=True), Comment(
                r"\*/", mode=DjJS, return_mode=self
            )
        elif raw_token.startswith("//"):
            token = Token.Text(raw_token, mode=DjJS, ignore=True)

        # "Double" tokens
        elif not line and raw_token.lstrip().startswith("case "):
            token = Token.OpenDouble(raw_token, mode=DjJS)
            return token, mode
        elif raw_token.rstrip().endswith("default:"):
            token = Token.OpenDouble(raw_token, mode=DjJS)
            return token, mode

        # Tokens that mess with relative offset
        elif raw_token.lstrip().startswith("..."):
            token = Token.Text(raw_token, mode=DjJS)
        elif not line and raw_token.lstrip().startswith((".", ": ", "? ")):
            token = Token.Text(raw_token, mode=DjJS, relative=1)
        elif not line and raw_token in ["if", "else", "for", "while"]:
            token = Token.Text(raw_token, mode=DjJS, **self.offsets)
            self.offsets["relative"] += 1
            persist_relative_offset = True
        elif raw_token.rstrip().endswith(("=", ":")):
            token = Token.Text(raw_token, mode=DjJS, **self.offsets)
            if not line.indents:
                self.offsets["relative"] = 1
                persist_relative_offset = True

        # Tokens that mess with absolute offset
        elif raw_token in ["var ", "let ", "const "]:
            token = Token.Text(raw_token, mode=DjJS)
            self.offsets["absolute"] = len(line) + len(raw_token)
        elif (
            not line
            and not self.haskell
            and not self.previous_line_ended_with_comma
            and self.haskell_re.match(raw_token)
        ):
            self.haskell = True
            self.offsets["absolute"] -= 2
            token = Token.Text(raw_token, mode=DjJS, **self.offsets)

        # Get out of this mess!
        elif raw_token == "</script>":
            token, mode = (
                Token.Close(raw_token, mode=self.return_mode.__class__),
                self.return_mode,
            )
        else:
            token, mode = super().create_token(raw_token, src, line)

        # Reset relative offset in almost all cases
        if not persist_relative_offset and raw_token.strip():
            self.offsets["relative"] = 0

        # Remember whether the line ended with a comma
        if raw_token.rstrip().endswith(","):
            self.previous_line_ended_with_comma = True
        else:
            self.previous_line_ended_with_comma = False

        return token, mode


# The following are "special" modes with different constructors.


class Comment(DjTXT):
    """
    Mode to create ignore tokens until an end tag is encountered.

    """

    def __init__(self, endtag, *, mode, return_mode):
        self.endtag = endtag
        self.mode = mode
        self.return_mode = return_mode
        self.token_re = compile_re([r"\n", endtag])

    def create_token(self, raw_token, src, line):
        if re.match(self.endtag, raw_token):
            return Token.Close(raw_token, mode=self.mode, ignore=True), self.return_mode
        return Token.Text(raw_token, mode=Comment, ignore=True), self


class InsideHTMLTag(DjTXT):
    """
    Welcome to the wondrous world between "<" and ">".

    """

    RAW_TOKENS = DjTXT.RAW_TOKENS + [r"/?>", r"[^ ='\">/\n]+=", r'"', r"'"]

    def __init__(self, tagname, line, return_mode, absolute, offsets):
        self.tagname = tagname
        self.return_mode = return_mode
        self.absolute = absolute
        self.offsets = offsets
        self.token_re = compile_re(self.RAW_TOKENS)
        self.inside_attr = False
        self.additional_offset = -len(tagname) - 1 if absolute else 0

    def create_token(self, raw_token, src, line):
        mode = self

        if not line:
            self.additional_offset = 0
        self.additional_offset += len(raw_token)

        if "text/template" in raw_token:
            self.tagname = ""

        if raw_token in ['"', "'"]:
            if self.inside_attr:
                token = Token.Text(raw_token, mode=InsideHTMLTag, **self.offsets)
                if self.inside_attr == raw_token:
                    self.inside_attr = False
                    token.absolute = self.offsets["absolute"] - 1
                    self.offsets["absolute"] = self.previous_offset
            else:
                self.inside_attr = raw_token
                self.previous_offset = self.offsets["absolute"]
                self.offsets["absolute"] += self.additional_offset
                token = Token.Text(raw_token, mode=InsideHTMLTag, **self.offsets)
        elif not self.inside_attr and raw_token == "/>":
            token, mode = Token.Text(raw_token, mode=DjHTML), self.return_mode
            if not self.absolute:
                token.dedents = True
        elif not self.inside_attr and raw_token == ">":
            if self.tagname.lower() in DjHTML.IGNORE_TAGS:
                token, mode = Token.Text(raw_token, mode=DjHTML), self.return_mode
            elif self.tagname == "style":
                token, mode = Token.Open(raw_token, mode=DjHTML), DjCSS(
                    return_mode=self.return_mode
                )
            elif self.tagname == "script":
                token, mode = Token.Open(raw_token, mode=DjHTML), DjJS(
                    return_mode=self.return_mode
                )
            else:
                token, mode = (
                    Token.Open(raw_token, mode=DjHTML),
                    self.return_mode,
                )
            if not self.absolute:
                token.dedents = True
        else:
            token, mode = super().create_token(raw_token, src, line)

        return token, mode


class MaxLineLengthExceeded(Exception):
    pass


def compile_re(raw_tokens):
    return re.compile("(" + "|".join(raw_tokens) + ")")
