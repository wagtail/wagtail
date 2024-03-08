class Token:
    """
    Container class for token types.

    """

    class _Base:
        indents = False
        dedents = False
        ignore = False
        is_double = False

        def __init__(
            self, text, *, mode, level=0, relative=0, absolute=0, ignore=False
        ):
            """
            Tokens must have a text and a mode class. The level
            represents the line level of opening tokens and is set
            afterwards by the parser. This violates the principle of
            encapsulation, but makes sense because the line level can
            only be determined after the tokenization is complete.

            """
            self.text = text
            self.mode = mode
            self.level = level
            self.relative = relative
            self.absolute = absolute
            self.ignore = ignore

        def __repr__(self):
            kwargs = f", mode={self.mode.__name__}"
            for attr in ["level", "relative", "absolute", "ignore"]:
                if value := getattr(self, attr):
                    kwargs += f", {attr}={value!r}"
            return f"{self.__class__.__name__}({self.text!r}{kwargs})"

    class Text(_Base):
        pass

    class Open(_Base):
        indents = True

    class OpenDouble(_Base):
        indents = True
        is_double = True

    class Close(_Base):
        dedents = True

    class CloseDouble(_Base):
        dedents = True
        is_double = True

    class CloseAndOpen(_Base):
        indents = True
        dedents = True
