import subprocess
import re
from collections import defaultdict

authors_by_locale = defaultdict(set)

file_listing = subprocess.Popen('find ../wagtail -iname *.po', shell=True, stdout=subprocess.PIPE)

for file_listing_line in file_listing.stdout:
    filename = file_listing_line.strip()

    # extract locale string from filename
    locale = re.search(r'locale/(\w+)/LC_MESSAGES', filename).group(1)
    if locale == 'en':
        continue

    # read author list from each file
    with file(filename) as f:
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

locales = sorted(authors_by_locale.keys())
for locale in locales:
    print(locale)
    print("-----")
    for author in sorted(authors_by_locale[locale]):
        print(author)
    print('')
