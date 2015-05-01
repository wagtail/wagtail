#! /bin/sh
# vim:sw=4 ts=4 et:

version=""
url="https://wagtail.io"

while [ ! -z "$1" ]; do
    case "$1" in
        --version=*)
            version=$(echo "$1" | sed -e 's/^--version=//')
            ;;
        --url=*)
            url=$(echo "$1" | sed -e 's/^--url=//')
            ;;
        *)
            printf >&2 -- '%s: unknown argument "%s"\n' "$0"
            printf >&2 -- 'usage: %s --version=<version> [--url=<url>]\n' "$0"
            exit 1
    esac
    shift
done

if [ -z "$version" ]; then
    printf >&2 -- '%s: must specify --version\n' "$0"
    printf >&2 -- 'usage: %s --version=<version> [--url=<url>]\n' "$0"
    exit 1
fi

LTMP=$(mktemp "${TMPDIR:-/tmp}/latest.XXXXXX")
if [ "$?" -ne 0 ]; then
    printf >&2 -- '%s: cannot create temporary file\n' "$0"
    exit 1
fi
trap 'rm -f "${LTMP}"' 0 TERM INT

cat >"${LTMP}" <<__EOF__
{
    "version": "${version}",
    "url":     "${url}"
}
__EOF__

${0%make-latest.sh}latest.sh put "${LTMP}"
