#! /bin/sh
# vim:sw=4 ts=4 et:

BUCKET=releases.wagtail.io
REGION=eu-west-1
CF_DISTRIBUTION=E283SZ5CB4MDM0

# Find the location of the AWS CLI binary.  MacPorts sometimes put it in a
# weird place, so to be helpful we check those locations as well.
if [ -z "${AWS_CLI}" ]; then
    for d in $(echo "${PATH}" | tr ':' ' ')                             \
        /opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin \
        /opt/local/Library/Frameworks/Python.framework/Versions/3.4/bin \
        ; do
        if [ -x "${d}/aws" ]; then
            AWS_CLI="${d}/aws"
            break
        fi
    done

    if [ -z "${AWS_CLI}" ]; then
        printf >&2 -- '%s: cannot find AWS CLI binary "aws"\n' "$0"
        printf >&2 -- '%s: please install AWS from https://aws.amazon.com/documentation/cli/\n' "$0"
        exit 1
    fi
fi

# CloudFront support in the CLI is still in beta.
$AWS_CLI configure set preview.cloudfront true

_usage() {
    printf >&2 -- 'usage: %s get       [output-filename]\n' "$0"
    printf >&2 -- '       %s put       [input-filename]\n' "$0"
    printf >&2 -- '       %s <vi|edit>\n' "$0"
}

if [ "$#" -lt 1 ]; then
    _usage
    exit 1
fi

_get() {
    if ! $AWS_CLI s3 cp --region "${REGION}" "s3://${BUCKET}/latest.txt" "$1"; then
        printf >&2 -- "%s: failed to download latest.txt; see above messages\\n" "$0"
        exit 1
    fi
}

_put() {
    if ! $AWS_CLI s3 cp --acl public-read --region "${REGION}" "$1" "s3://${BUCKET}/latest.txt"; then
        printf >&2 -- "%s: failed to upload latest.txt; see above messages\\n" "$0"
        exit 1
    fi

    $AWS_CLI >/dev/null cloudfront create-invalidation  \
        --distribution-id "$CF_DISTRIBUTION"            \
        --invalidation-batch                            \
'{
    "Paths": {
        "Items": [
            "/latest.txt"
        ],
    "Quantity": 1
    },
    "CallerReference": "latest.sh"
}'
}

if [ "$1" = "get" ]; then
    if [ "$#" -lt 2 ]; then
        _usage
        exit 1
    fi

    shift

    if [ -e "$2" ]; then
        printf >&2 -- "%s: \"%s\": already exists, won't overwrite\\n" "$0"
        exit 1
    fi

    _get "$@"
elif [ "$1" = "put" ]; then
    if [ "$#" -lt 2 ]; then
        _usage
        exit 1
    fi

    shift

    _put "$@"
elif [ "$1" = "edit" -o "$1" = "vi" ]; then
    LTMP=$(mktemp "${TMPDIR:-/tmp}/latest.XXXXXX")
    if [ "$?" -ne 0 ]; then
        printf >&2 -- '%s: cannot create temporary file\n' "$0"
        exit 1
    fi
    trap 'rm -f "${LTMP}"' 0 TERM INT

    LTMP2=$(mktemp "${TMPDIR:-/tmp}/latest.XXXXXX")
    if [ "$?" -ne 0 ]; then
        printf >&2 -- '%s: cannot create temporary file\n' "$0"
        exit 1
    fi
    trap 'rm -f "${LTMP2}"' 0 TERM INT

    if ! _get "${LTMP}"; then
        exit 1
    fi

    cp "${LTMP}" "${LTMP2}"

    if [ ! -z "${VISUAL}" ]; then
        editor="${VISUAL}"
    elif [ ! -z "${EDITOR}" ]; then
        editor="${EDITOR}"
    else
        editor='vi'
    fi

    $editor "${LTMP}"
    if cmp "${LTMP}" "${LTMP2}" >/dev/null; then
        printf >&2 -- '%s: no changes; exiting\n' "$0"
        exit
    fi

    diff -u "${LTMP2}" "${LTMP}"
    _put "${LTMP}"
fi
