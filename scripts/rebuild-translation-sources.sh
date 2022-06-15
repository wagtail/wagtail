# Delete old translation sources
find ../wagtail -iname *.po -iwholename */en/* -delete

# Run makemessages on each app
for d in $(find ../wagtail -iwholename */locale/* | sed 's|\(.*\)/locale.*|\1|' | sort -u);
do
    pushd $d
    django-admin makemessages --locale=en --ignore=test/* --ignore=tests/* --ignore=tests.py
    popd
done

# Extract translatable strings from JavaScript
pushd ../client
node extract-translatable-strings.js
popd
