from threading import RLock

import core


_MODE_CLOSED = 0
_MODE_READ = 1
_MODE_WRITE = 2


class EncodedFile(object):
    def __init__(self, filename=None, mode=None,
                 _fp=None, **compress_options):
        self._lock = RLock()
        self._mode = _MODE_CLOSED
        self._compress_options = compress_options

        if filename:
            self._fp = open(filename, mode)
        elif _fp:
            self._fp = _fp
        else:
            raise ValueError('No filename or file object provided')

        if mode in ('', 'r', 'rb'):
            mode = 'rb'
            self._mode = _MODE_READ
        elif mode in ('w', 'wb'):
            mode = 'wb'
            self._mode = _MODE_WRITE
        else:
            raise ValueError('Invalid mode: {}'.format(mode))

        # File seek position
        self._pos = 0
        # Name of file
        self.name = self._fp.name

    def close(self):
        with self._lock:
            if not self.closed:
                self._mode = _MODE_CLOSED
                self._fp.close()
                self._fp = None

    @property
    def closed(self):
        return self._mode == _MODE_CLOSED

    def fileno(self):
        return self._fp.fileno()

    def seekable(self):
        """Return whether the file supports seeking."""
        return self.readable()

    def readable(self):
        """Return whether the file was opened for reading."""
        return self._mode == _MODE_READ

    def writeable(self):
        return self._mode == _MODE_WRITE

    def read(self, size=-1):
        """Read up to size uncompressed bytes from the file.

        If size is negative or omitted, read until EOF is reached.
        Returns b'' if the file is already at EOF.
        """
        with self._lock:
            # Actually read from buffer
            pass

    def readinto(self, b):
        """Read bytes into b.

        Returns the number of bytes read (0 for EOF).
        """
        with self._lock:
            pass

    def readline(self, size=-1):
        """Read a line of uncompressed bytes from the file.

        The terminating newline (if present) is retained. If size is
        non-negative, no more than size bytes will be read (in which
        case the line may be incomplete). Returns b'' if already at EOF.
        """
        with self._lock:
            pass

    def readlines(self, size=-1):
        """Read a list of lines of uncompressed bytes from the file.

        size can be specified to control the number of lines read; no
        further lines will be read once the total size of the lines read
        so far equals or exceeds size.
        """
        with self._lock:
            pass

    def write(self, data):
        """Write a byte string to the file.

        Returns the number of uncompressed bytes written, which is
        always len(data). Note that due to buffering, the file on disk
        may not reflect the data written until close() is called.
        """
        with self._lock:
            compressed = core.encode(data, **self._compress_options)
            self._fp.write(compressed)
            self._pos += len(data)
            return len(data)

    def writelines(self, seq):
        """Write a sequence of byte strings to the file.

        Returns the number of uncompressed bytes written.
        seq can be any iterable yielding byte strings.

        Line separators are not added between the written byte strings."""
        with self._lock:
            pass

    def seek(self, offset, whence=0):
        """Change the file position.

        The new position is specified by offset, relative to the
        position indicated by whence. Values for whence are:

            0: start of stream(default); offset must not be negative
            1: current stream position
            2: end of stream; offset must not be positive

        Returns the new file position.
        """
        with self._lock:
            pass

    def tell(self):
        """Return the current file position."""
        with self._lock:
            if self._mode == _MODE_READ:
                pass
            return self._pos


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
        binary_file = EncodedFile(_fp=file, mode=mode, **kwargs)
    else:
        raise TypeError('file must be an str, unicode or file-like object')
    return binary_file
