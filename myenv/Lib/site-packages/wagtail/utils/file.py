import hashlib
from io import UnsupportedOperation

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

    if hasattr(hashlib, "file_digest"):
        hasher = hashlib.file_digest(filelike, hashlib.sha1)
    else:
        hasher = hashlib.sha1()
        while True:
            data = filelike.read(HASH_READ_SIZE)
            if not data:
                break
            hasher.update(data)

    if hasattr(filelike, "seek"):
        # Reset the file handler to where it was before
        filelike.seek(file_pos)

    return hasher.hexdigest()
