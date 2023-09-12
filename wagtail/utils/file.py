import hashlib
from io import UnsupportedOperation

from django.utils.encoding import force_bytes

HASH_READ_SIZE = 2**18  # 256k - matches `hashlib.file_digest`


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

    hasher = None

    if hasattr(hashlib, "file_digest"):
        try:
            hasher = hashlib.file_digest(filelike, hashlib.sha1)
        except ValueError:
            # If the value can't be accepted by `file_digest` (eg text-mode files), use our fallback implementation
            pass

    if hasher is None:
        hasher = hashlib.sha1()
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
