import re
from pathlib import Path

import polib

placeholder_regexp = re.compile(r"\{[^\}]*?\}")

for path in Path(__file__).parent.resolve().parent.rglob("LC_MESSAGES/*.po"):
    po = polib.pofile(path)
    for entry in po:
        if not entry.msgstr:
            continue  # ignore untranslated strings

        expected_placeholders = set(placeholder_regexp.findall(entry.msgid))
        actual_placeholders = set(placeholder_regexp.findall(entry.msgstr))
        if expected_placeholders != actual_placeholders:
            print("Invalid string at %s line %d:" % (path, entry.linenum))  # noqa
            print(  # noqa
                "\toriginal string %r has placeholders: %r"
                % (entry.msgid, expected_placeholders)
            )  # noqa
            print(  # noqa
                "\ttranslated string %r has placeholders: %r"
                % (entry.msgstr, actual_placeholders)
            )  # noqa
            print()  # noqa
