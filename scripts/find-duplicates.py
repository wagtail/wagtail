"""
Utility script to find strings marked for translation that are
in the form:
'Change Password' -> 'change password'
In order to minimize translation efforts, only one should be used.
It uses babel instead more standard 'polib' because it's used in another script.
"""
from __future__ import print_function

import glob
from babel.messages.pofile import read_po


def check(mess, othermess):
    return mess.id.lower() == othermess.id.lower()


def find_duplicates_in_file(filepath):
    fileobj = open(filepath)
    catalog = read_po(fileobj)

    already_found = []
    for mess in catalog:
        for othermess in catalog:
            # Tuples are plurals, we only consider single translations
            if isinstance(mess.id, str) and isinstance(othermess.id, str):
                if mess.id != othermess.id and check(mess, othermess) and mess.id.lower() not in already_found:
                    already_found.append(mess.id.lower())
                    yield mess, othermess
                    break


def print_output(message, othermessage):
    print("'{}' --> {} \n {} --> {}.\n -----".format(
        message.id, message.locations,
        othermessage.id, othermessage.locations
    ))

if __name__ == "__main__":
    translations_paths = glob.glob('../wagtail/*/LOCALE/en/LC_MESSAGES/*.po')

    for filepath in translations_paths:
        for message, othermessage in find_duplicates_in_file(filepath):
            if message:
                print(filepath)
                print_output(message, othermessage)


