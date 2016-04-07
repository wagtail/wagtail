# Delete old translation files (except "en" which is the source translation)
find ../wagtail -iname *.po ! -iwholename */en/* -delete

# Fetch new translations from transifex
tx pull -a --minimum-perc=1

# Clean the PO files using msgattrib
# This removes the following:
#  - Blank, fuzzy and obsolete translations
#  - The line numbers above each translation
# These things are only needed by translators (which they won't be seen by) and make the translation updates difficult to check
find ../wagtail -iname *.po ! -iwholename */en/* -exec msgattrib --translated --no-fuzzy --no-obsolete --no-location -o {} {} \;

# Run compilemessages on each app
for d in $(find ../wagtail -iname *.po | sed 's|\(.*\)/locale.*|\1|' | sort -u);
do
    pushd $d
    django-admin compilemessages
    popd
done
