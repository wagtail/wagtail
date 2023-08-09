from hashlib import sha1
from io import UnsupportedOperation

from django.utils.encoding import force_bytes

HASH_READ_SIZE = 65536  # 64k


def hash_filelike(filelike):
    """
    Compute the hash of a file-like object, without loading it all into memory.
    """
    file_pos = 0
    if hasattr(filelike, "tell"):
        file_pos = filelike.tell()

    try:
        # Reset file handler to the start of the file so we hash it all
        filelike.seek(0)
    except (AttributeError, UnsupportedOperation):
        pass

    hasher = sha1()
    while True:
        data = filelike.read(HASH_READ_SIZE)
        if not data:
            break
        # Use `force_bytes` to account for files opened as text
        hasher.update(force_bytes(data))

    if hasattr(filelike, "seek"):
        # Reset the file handler to where it was before
        filelike.seek(file_pos)

    return hasher.hexdigest()
