#!/usr/bin/env python
# -*- coding: utf-8
"""
Write a list of translators in the TRANSLATORS_FILE file.
"""
from __future__ import print_function, unicode_literals

import subprocess
import re
from collections import defaultdict
from io import open

from babel import Locale

TRANSLATORS_FILE = '../TRANSLATORS.rst'
CORE_DEVELOPERS = ['Matt Westcott', ]


def author_name(author):
    return re.sub('<.*?>', '', author).strip()


def is_core_developer(author):
    return author_name(author) in CORE_DEVELOPERS


authors_by_locale = defaultdict(set)

file_listing = subprocess.Popen('find ../wagtail -iname *.po', shell=True, stdout=subprocess.PIPE)

for file_listing_line in file_listing.stdout:
    filename = file_listing_line.strip()

    # extract locale string from filename
    locale = re.search(r'locale/(\w+)/LC_MESSAGES', str(filename)).group(1)
    if locale == 'en':
        continue

    # read author list from each file
    with open(filename, 'rt') as f:
        has_found_translators_heading = False
        for line in f:
            line = line.strip()
            if line.startswith('#'):
                if has_found_translators_heading:
                    author = re.match(r'\# (.*), [\d\-]+', line).group(1)
                    authors_by_locale[locale].add(author)
                elif line.startswith('# Translators:'):
                    has_found_translators_heading = True
            else:
                if has_found_translators_heading:
                    break
                else:
                    raise Exception("No 'Translators:' heading found in %s" % filename)

language_names = [
    (Locale.parse(locale_string).english_name, locale_string)
    for locale_string in authors_by_locale.keys()
]
language_names.sort()

with open(TRANSLATORS_FILE, 'w', encoding='utf-8') as f:
    f.write('Translators\n')
    f.write('===========\n')
    f.write('\n')
    for (language_name, locale) in language_names:
        authors = [author for author in sorted(authors_by_locale[locale]) if not is_core_developer(author)]
        f.write("* {}: {}\n".format(language_name, ', '.join([author_name(author) for author in authors])))

