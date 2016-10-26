import io

import core


_READ_MODE = 0
_WRITE_MODE = 1


class EncodedFile(io.BufferedIOBase):
    def __init__(self, filename=None, mode=None,
                 fileobj=None, **compress_options):
        pass


def open(file, mode='rb', **kwargs):
    """
    Open file and return the correspoding EncodedFile object.

    file is either a string or unicode representing a file path
    or a file-like object.
    """
    if isinstance(file, (unicode, str)):
        binary_file = EncodedFile(file, mode)
    # Implements the file protocol
    elif hasattr(file, 'read') or hasattr(file, 'write'):
        binary_file = EncodedFile(fileobj=file, mode=mode, **kwargs)
    else:
        raise TypeError('file must be an str, unicode or file-like object')
    return binary_file
