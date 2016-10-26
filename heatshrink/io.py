from threading import RLock
import io

import core

BUFFER_SIZE = io.DEFAULT_BUFFER_SIZE


class DecompressReader(io.RawIOBase):
    def __init__(self, fp, decomp_fn, **decomp_args):
        self._fp = fp
        self._eof = False
        self._pos = 0  # Current offset in decompressed stream

        # Set to size of decompressed stream once it is known
        self._size = -1

        self._decomp_fn = decomp_fn
        self._decomp_args = decomp_args

    def close(self):
        return super(EncodedFile).close()

    def readable(self):
        return True

    def seekable(self):
        return self._fp.seekable()

    def readinto(self, b):
        with memoryview(b) as view, view.cast('B') as byte_view:
            data = self.read(len(byte_view))
            byte_view[:len(data)] = data
        return len(data)

    def read(self, size=-1):
        if size < 0:
            return self.readall()

        if not size or self._eof:
            return b''

        raw_chunk = self._fp.read(size)
        if raw_chunk:
            data = self._decomp_fn(raw_chunk, **self._decomp_args)
        else:
            data = None

        if not data:
            self._eof = True
            self._size = self._pos
            return b''
        self._pos += len(data)
        return data

    # Rewind the file to the beginning of the data stream.
    def _rewind(self):
        self._fp.seek(0)
        self._eof = False
        self._pos = 0

    def seek(self, offset, whence=io.SEEK_SET):
        if whence == io.SEEK_SET:
            pass
        elif whence == io.SEEK_CUR:
            offset += self._pos
        elif whence == io.SEEK_END:
            if self._size < 0:
                # Finish reading the file
                while self.read(io.DEFAULT_BUFFER_SIZE):
                    pass
            offset += self._size
        else:
            raise ValueError('Invalid value for whence: {}'.format(whence))

        # Make it so that offset is the number of bytes to skip forward.
        if offset < self._pos:
            self._rewind()
        else:
            offset -= self._pos

        # Read and discard data until we reach the desired position
        while offset > 0:
            data = self.read(min(io.DEFAULT_BUFFER_SIZE, offset))
            if not data:
                break
            offset -= len(data)

        return self._pos

    def tell(self):
        return self._pos


_MODE_CLOSED = 0
_MODE_READ = 1
_MODE_WRITE = 2


class EncodedFile(io.BufferedIOBase):
    def __init__(self, filename=None, mode=None,
                 _fp=None, **compress_options):
        self._lock = RLock()
        self._mode = _MODE_CLOSED

        if filename:
            self._fp = open(filename, mode)
        elif _fp:
            self._fp = _fp
        else:
            raise ValueError('No filename or file object provided')

        if mode in ('', 'r', 'rb'):
            mode = 'rb'
            self._mode = _MODE_READ
            self._buffer = DecompressReader(self._fp, core.decode,
                                            **compress_options)
        elif mode in ('w', 'wb'):
            mode = 'wb'
            self._mode = _MODE_WRITE
        else:
            raise ValueError('Invalid mode: {}'.format(mode))

        # File seek position
        self._pos = 0
        # Set to size of the decompressed stream once it is known
        self._size = -1
        # True if reached EOF
        self._eof = False
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
            self._buffer.read(size)

    def read1(self, size=-1):
        """Read up to size uncompressed bytes, while trying to avoid
        making multiple reads from the underlying stream. Reads up to a
        buffers worth of data if size is negative.

        Returns b'' if the file is at EOF.
        """
        with self._lock:
            if size < 0:
                size = io.DEFAULT_BUFFER_SIZE
            return self._buffer.read1(size)

    def readinto(self, b):
        """Read bytes into b.

        Returns the number of bytes read (0 for EOF).
        """
        with self._lock:
            return self._buffer.readinto(b)

    def readline(self, size=-1):
        """Read a line of uncompressed bytes from the file.

        The terminating newline (if present) is retained. If size is
        non-negative, no more than size bytes will be read (in which
        case the line may be incomplete). Returns b'' if already at EOF.
        """
        with self._lock:
            return self._buffer.readline(size)

    def readlines(self, size=-1):
        """Read a list of lines of uncompressed bytes from the file.

        size can be specified to control the number of lines read; no
        further lines will be read once the total size of the lines read
        so far equals or exceeds size.
        """
        with self._lock:
            return self._buffer.readlines(size)

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
            return super(EncodedFile, self).writelines(seq)

    def seek(self, offset, whence=io.SEEK_SET):
        """Change the file position.

        The new position is specified by offset, relative to the
        position indicated by whence. Values for whence are:

            0: start of stream(default); offset must not be negative
            1: current stream position
            2: end of stream; offset must not be positive

        Returns the new file position.
        """
        with self._lock:
            self._buffer.seek(offset, whence)

    def tell(self):
        """Return the current file position."""
        with self._lock:
            if self._mode == _MODE_READ:
                return self._buffer.tell()
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
