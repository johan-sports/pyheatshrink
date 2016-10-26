import io

import core


class EncodedFile(io.BufferedIOBase):
    def __init__(self, filename=None, mode=None,
                 fileobj=None, **compress_options):
        pass


def open(filename, mode='rb', **kwargs):
    if isinstance(filename, (unicode, str)):
        pass
