import string


MAX_QUERY_STRING_LENGTH = 255


def normalise_query_string(query_string):
    # Truncate query string
    if len(query_string) > MAX_QUERY_STRING_LENGTH:
        query_string = query_string[:MAX_QUERY_STRING_LENGTH]
    # Convert query_string to lowercase
    query_string = query_string.lower()

    # Strip punctuation characters
    query_string = ''.join([c for c in query_string if c not in string.punctuation])

    # Remove double spaces
    query_string = ' '.join(query_string.split())

    return query_string
