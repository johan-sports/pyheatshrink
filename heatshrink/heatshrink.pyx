import io
import sys
import __builtin__

import array
import numbers
cimport cython
from cpython cimport array
from libc.stdint cimport uint8_t

cimport cheatshrink

MIN_WINDOW_SZ2 = cheatshrink.HEATSHRINK_MIN_WINDOW_BITS
MAX_WINDOW_SZ2 = cheatshrink.HEATSHRINK_MAX_WINDOW_BITS
DEFAULT_WINDOW_SZ2 = 11

MIN_LOOKAHEAD_SZ2 = cheatshrink.HEATSHRINK_MIN_LOOKAHEAD_BITS
DEFAULT_LOOKAHEAD_SZ2 = 4

DEFAULT_INPUT_BUFFER_SIZE = 2048


cdef validate_bounds(val, name, min=None, max=None):
    """
    Ensure that `val` is larger than `min` and smaller than `max`.

    Throws `ValueError` if constraints are not met or
    if both `min` and `max` are None.
    Throws `TypeError` if `val` is not a number.
    """
    if min is None and max is None:
        raise ValueError("Expecting either a min or max parameter")

    if not isinstance(val, numbers.Number):
        msg = 'Expected number, got {}'
        raise TypeError(msg.format(val.__class__.__name__))

    if min and val < min:
        msg = "{} must be > {}".format(name, min)
    elif max and val > max:
        msg = "{} must be < {}".format(name, max)
    else:
        msg = ''

    if msg:
        raise ValueError(msg)
    return val


cdef class Writer:
    """Thin wrapper around heatshrink_encoder"""
    cdef cheatshrink.heatshrink_encoder *_hse

    def __cinit__(self, window_sz2, lookahead_sz2):
        validate_bounds(window_sz2, name='window_sz2',
                        min=MIN_WINDOW_SZ2, max=MAX_WINDOW_SZ2)
        validate_bounds(lookahead_sz2, name='lookahead_sz2',
                        min=MIN_LOOKAHEAD_SZ2, max=window_sz2)

        self._hse = cheatshrink.heatshrink_encoder_alloc(window_sz2, lookahead_sz2)
        if self._hse is NULL:
            raise MemoryError

    def __dealloc__(self):
        if self._hse is not NULL:
            cheatshrink.heatshrink_encoder_free(self._hse)

    cdef cheatshrink.HSE_sink_res sink(self, uint8_t *in_buf, size_t size, size_t *input_size) nogil:
        return cheatshrink.heatshrink_encoder_sink(self._hse, in_buf, size, input_size)

    @property
    def max_output_size(self):
        return 1 << self._hse.window_sz2

    cdef cheatshrink.HSE_poll_res poll(self, uint8_t *out_buf, size_t out_buf_size, size_t *output_size) nogil:
        return cheatshrink.heatshrink_encoder_poll(self._hse, out_buf, out_buf_size, output_size)

    cdef is_poll_empty(self, cheatshrink.HSE_poll_res res):
        return res == cheatshrink.HSER_POLL_EMPTY

    cdef finish(self):
        return cheatshrink.heatshrink_encoder_finish(self._hse)

    cdef is_finished(self, cheatshrink.HSE_finish_res res):
        return res == cheatshrink.HSER_FINISH_DONE


cdef class Reader:
    """Thin wrapper around heatshrink_decoder"""
    cdef cheatshrink.heatshrink_decoder *_hsd

    def __cinit__(self, input_buffer_size, window_sz2, lookahead_sz2):
        validate_bounds(input_buffer_size, name='input_buffer_size', min=0)
        validate_bounds(window_sz2, name='window_sz2',
                        min=MIN_WINDOW_SZ2, max=MAX_WINDOW_SZ2)
        validate_bounds(lookahead_sz2, name='lookahead_sz2',
                        min=MIN_LOOKAHEAD_SZ2, max=window_sz2)

        self._hsd = cheatshrink.heatshrink_decoder_alloc(
            input_buffer_size, window_sz2, lookahead_sz2)
        if self._hsd is NULL:
            raise MemoryError

    def __dealloc__(self):
        if self._hsd is not NULL:
            cheatshrink.heatshrink_decoder_free(self._hsd)

    cdef cheatshrink.HSD_sink_res sink(self, uint8_t *in_buf, size_t size, size_t *input_size) nogil:
        return cheatshrink.heatshrink_decoder_sink(self._hsd, in_buf, size, input_size)

    @property
    def max_output_size(self):
        return 1 << self._hsd.window_sz2

    cdef cheatshrink.HSD_poll_res poll(self, uint8_t *out_buf, size_t out_buf_size, size_t *output_size) nogil:
        return cheatshrink.heatshrink_decoder_poll(self._hsd, out_buf, out_buf_size, output_size)

    cdef is_poll_empty(self, cheatshrink.HSD_poll_res res):
        return res == cheatshrink.HSDR_POLL_EMPTY

    cdef finish(self):
        return cheatshrink.heatshrink_decoder_finish(self._hsd)

    cdef is_finished(self, cheatshrink.HSD_finish_res res):
        return res == cheatshrink.HSDR_FINISH_DONE


# When used as a function parameter, it will generate one C
# function for each type defined.
ctypedef fused Encoder:
    Reader
    Writer


cdef size_t sink(Encoder obj, array.array in_buf, size_t offset=0):
    """
    Sink input in to the encoder with an optional N byte `offset`.
    """
    cdef size_t sink_size

    res = obj.sink(&in_buf.data.as_uchars[offset],
                   len(in_buf) - offset, &sink_size)
    if res < 0:
        raise RuntimeError('Sink failed.')

    return sink_size


cdef poll(Encoder obj):
    """
    Poll output from an encoder/decoder.

    Returns a tuple containing the poll output buffer
    and a boolean indicating if polling is finished.
    """
    cdef size_t poll_size

    cdef array.array out_buf = array.array('B', [])
    # Resize to a decent length
    array.resize(out_buf, obj.max_output_size)

    res = obj.poll(out_buf.data.as_uchars, len(out_buf), &poll_size)
    if res < 0:
        raise RuntimeError('Polling failed.')

    # Resize to drop unused elements
    array.resize(out_buf, poll_size)

    done = obj.is_poll_empty(res)
    return (out_buf, done)


cdef finish(Encoder obj):
    """
    Notifies the encoder that the input stream is finished.

    Returns `False` if there is more ouput to be processed,
    meaning that poll should be called again.
    """
    res = obj.finish()
    if res < 0:
        raise RuntimeError("Finish failed.")
    return obj.is_finished(res)


cdef encode_impl(Encoder obj, buf):
    """Encode iterable `buf` into an array of bytes."""
    # HACK: Mitigate python 2 issues with value `Integer is required`
    # HACK: error messages for some types of objects.
    if isinstance(buf, unicode) or isinstance(buf, memoryview):
        msg = "cannot use {.__name__} to initialize an array with typecode 'B'"
        raise TypeError(msg.format(buf.__class__))

    # Convert input to a byte representation
    cdef array.array byte_buf = array.array('B', buf)

    cdef size_t total_sunk_size = 0
    cdef array.array encoded = array.array('B', [])

    while True:
        if total_sunk_size < len(byte_buf):
            total_sunk_size += sink(obj, byte_buf, total_sunk_size)

        while True:
            polled, done = poll(obj)
            # TODO: Optimize this
            encoded.extend(polled)
            if done:
                break

        if total_sunk_size >= len(byte_buf):
            # If the encoder isn't finished we need to re-poll
            if finish(obj):
                break

    try:
        # Python 3
        return encoded.tobytes()
    except AttributeError:
        return encoded.tostring()



def encode(buf, **kwargs):
    """
    Encode iterable `buf` in to a byte string.

    Keyword arguments:
        window_sz2 (int): Determines how far back in the input can be
            searched for repeated patterns. Defaults to `DEFAULT_WINDOW_SZ2`.
            Allowed values are between. `MIN_WINDOW_SZ2` and `MAX_WINDOW_SZ2`.
        lookahead_sz2 (int): Determines the max length for repeated
            patterns that are found. Defaults to `DEFAULT_LOOKAHEAD_SZ2`.
            Allowed values are between `MIN_LOOKAHEAD_SZ2` and the
            value set for `window_sz2`.

    Returns:
        str or bytes: A byte string of encoded contents.
            str is used for Python 2 and bytes for Python 3.

    Raises:
        ValueError: If `window_sz2` or `lookahead_sz2` are outside their
            defined ranges.
        TypeError: If `window_sz2`, `lookahead_sz2` are not valid numbers and
            if `buf` is not a valid iterable.
        RuntimeError: Thrown if internal polling or sinking of the
            encoder/decoder fails.
    """

    encode_params = {
        'window_sz2': DEFAULT_WINDOW_SZ2,
        'lookahead_sz2': DEFAULT_LOOKAHEAD_SZ2,
    }
    encode_params.update(kwargs)

    encoder = Writer(encode_params['window_sz2'],
                     encode_params['lookahead_sz2'])
    return encode_impl(encoder, buf)


def decode(buf, **kwargs):
    """
    Decode iterable `buf` in to a byte string.

    Keyword arguments:
        input_buffer_size (int): How large an input buffer to use for the decoder.
            This impacts how much work the decoder can do in a single step,
            a larger buffer will use more memory.
        window_sz2 (int): Determines how far back in the input can be
            searched for repeated patterns. Defaults to `DEFAULT_WINDOW_SZ2`.
            Allowed values are between. `MIN_WINDOW_SZ2` and `MAX_WINDOW_SZ2`.
        lookahead_sz2 (int): Determines the max length for repeated
            patterns that are found. Defaults to `DEFAULT_LOOKAHEAD_SZ2`.
            Allowed values are between `MIN_LOOKAHEAD_SZ2` and the
            value set for `window_sz2`.

    Returns:
        str or bytes: A byte string of decoded contents.
            str is used for Python 2 and bytes for Python 3.

    Raises:
        ValueError: If `input_buffer_size`, `window_sz2` or `lookahead_sz2` are
            outside their defined ranges.
        TypeError: If `input_buffer_size`, `window_sz2` or `lookahead_sz2` are
            not valid numbers and if `buf` is not a valid iterable.
        RuntimeError: Thrown if internal polling or sinking of the
            encoder/decoder fails.
    """
    encode_params = {
        'input_buffer_size': DEFAULT_INPUT_BUFFER_SIZE,
        'window_sz2': DEFAULT_WINDOW_SZ2,
        'lookahead_sz2': DEFAULT_LOOKAHEAD_SZ2,
    }
    encode_params.update(kwargs)

    decoder = Reader(encode_params['input_buffer_size'],
                     encode_params['window_sz2'],
                     encode_params['lookahead_sz2'])
    return encode_impl(decoder, buf)



_MODE_READ = 1
_MODE_WRITE = 2


class EncodedFile(io.BufferedIOBase):
    """
    The EncodedFile class simulates most of the methods of a file object with
    the exception of the readinto() and truncate() methods.
    """

    fileobj = None
    max_read_chunk = 5 * 1024 * 1024  # 5Mb

    def __init__(self, filename=None, mode=None,
                 fileobj=None, **compress_options):
        self.compress_options = compress_options
        # guarantee that the file is opened in binary mode on platforms
        # that care about that kind of thing.
        if mode and 'b' not in mode:
            mode += 'b'
        if fileobj is None:
            fileobj = __builtin__.open(filename, mode or 'rb')
        if filename is None:
            if hasattr(fileobj, 'name') and fileobj.name != '<fdopen>':
                filename = fileobj.name
            else:
                filename = ''
        if mode is None:
            if hasattr(fileobj, 'mode'):
                mode = fileobj.mode
            else:
                mode = 'rb'

        if mode[0:1] == 'r':
            self.mode = _MODE_READ
            # Set flag indicating the start of a new member
            self._new_member = True
            # Buffer data from file.
            self.extrabuf = ''
            # Number of bytes remaining in buffer from current
            # stream position.
            self.extrasize = 0
            # Offset in stream where buffer starts.
            self.extrastart = 0
            self.name = filename
            # Starts small, scales exponentially
            self.min_readsize = 100
        elif mode[0:1] == 'w' or mode[0:1] == 'a':
            self.mode = _MODE_WRITE
            self._init_write(filename)
        else:
            msg = 'Mode {} not supported'
            raise IOError(msg.format(mode))

        self.fileobj = fileobj
        self.offset = 0

    def __repr__(self):
        s = repr(self.fileobj)
        return '<EncodedFile ' + s[1:-1] + '>'

    def _check_not_closed(self):
        """
        Raises a ValueError if the underlying file object has been closed.
        """
        if self.closed:
            raise ValueError('I/O operation on closed file.')

    def _init_write(self, filename):
        """
        Prepare EncodedFile for writing to a file.
        """
        self.name = filename
        self.size = 0
        self.writebuf = []
        self.bufsize = 0

    def _init_read(self):
        self.size = 0

    def write(self, data):
        self._check_not_closed()
        if self.mode != _MODE_WRITE:
            import errno
            raise IOError(errno.EBADF, 'write() on read-only EncodedFile object')

        if self.fileobj is None:
            raise ValueError('write() on closed EncodedFile object')

        # Convert data type if called by io.BufferedWriter
        if isinstance(data, memoryview):
            data = data.tobytes()

        if len(data) > 0:
            self.fileobj.write(encode(data, **self.compress_options))
            self.size += len(data)
            self.offset += len(data)

        return len(data)

    def read(self, size=-1):
        self._check_not_closed()
        if self.mode != _MODE_READ:
            import errno
            raise IOError(errno.EBADF, 'read() on write-only EncodedFile object')

        if self.extrasize <= 0 and self.fileobj is None:
            return ''

        readsize = 1024
        if size < 0:  # get the whole thing
            try:
                while True:
                    self._read(readsize)
                    readsize = min(self.max_read_chunk, readsize * 2)
            except EOFError:
                size = self.extrasize
        else:  # just get some more of it
            try:
                while size > self.extrasize:
                    self._read(readsize)
                    readsize = min(self.max_read_chunk, readsize * 2)
            except EOFError:
                if size > self.extrasize:
                    size = self.extrasize

        offset = self.offset - self.extrastart
        chunk = self.extrabuf[offset: offset + size]
        self.extrasize -= size

        self.offset += size
        return chunk

    def _unread(self, buf):
        """
        Revert reading the given buffer.
        """
        self.extrasize += len(buf)
        self.offset -= len(buf)

    def _read(self, size=1024):
        if self.fileobj is None:
            raise EOFError('Reached EOF')

        if self._new_member:
            pos = self.fileobj.tell()  # Save current position
            self.fileobj.seek(0, 2)    # Seek to end of file
            if pos == self.fileobj.tell():
                raise EOFError('Reached EOF')
            else:
                self.fileobj.seek(pos)  # Return to original position

            self._init_read()
            self._new_member = False

        # Read chunk of data from the file
        buf = self.fileobj.read(size)

        if buf == '':
            raise EOFError('Reached EOF')

        uncompress = decode(buf, **self.compress_options)
        self._add_read_data(uncompress)

    def _add_read_data(self, data):
        offset = self.offset - self.extrastart
        self.extrabuf = self.extrabuf[offset:] + data
        self.extrasize += len(data)
        self.extrastart = self.offset
        self.size += len(data)

    @property
    def closed(self):
        return self.fileobj is None

    def close(self):
        fileobj = self.fileobj
        if fileobj is None:
            return
        self.fileobj = None
        fileobj.close()

    def flush(self):
        self._check_not_closed()
        if self.mode == _MODE_WRITE:
            self.fileobj.flush()

    def fileno(self):
        return self.fileobj.fileno()

    def rewind(self):
        """
        Reset file back to the beginning.
        """
        if self.mode != _MODE_READ:
            raise IOError("Can't rewind in write mode")
        self.fileobj.seek(0)
        self._new_member = True
        self.extrabuf = ''
        self.extrasize = 0
        self.extrastart = 0
        self.offset = 0

    def readable(self):
        """
        Returns true if the file can be read from.
        """
        return self.mode == _MODE_READ

    def writeable(self):
        """
        Returns true if the file can be written to.
        """
        return self.mode == _MODE_WRITE

    def seekable(self):
        return True

    def seek(self, offset, whence=0):
        if whence:
            if whence == 1:
                offset = self.offset + offset
            else:
                raise ValueError('Seek from end not supported')
        if self.mode == _MODE_WRITE:
            if offset < self.offset:
                raise IOError('Negative seek in write mode')
            count = offset - self.offset
            for i in xrange(count // 1024):
                self.write(1024 * '\0')
            self.write((count % 1024) * '\0')
        elif self.mode == _MODE_READ:
            if offset < self.offset:
                # for negative seek, rewind and do positive seek
                self.rewind()
            count = offset - self.offset
            for i in xrange(count // 1024):
                self.read(1024)
            self.read(count % 1024)

        return self.offset

    def readline(self, size=-1):
        if size < 0:
            # Shortcut common case - newline found in buffer
            offset = self.offset - self.extrastart
            i = self.extrabuf.find('\n', offset) + 1
            if i > 0:
                self.extrasize -= i - offset
                self.offset += i - offset
                return self.extrabuf[offset:i]

            size = sys.maxint
            readsize = self.min_readsize
        else:
            readsize = size
        bufs = []
        while size != 0:
            c = self.read(readsize)
            i = c.find('\n')
            # We set i=size to break out of the loop under two
            # conditions: 1) there's no newline, and the chunk is
            # larger than size, or 2) there is a newline, but the
            # resulting line would be longer than 'size'.
            if (size <= i) or (i == -1 and len(c) > size):
                i = size - 1

            if i >= 0 or c == '':
                bufs.append(c[:i + 1])  # Add portion of last chunk

                self._unread(c[i + 1:])  # Push back rest of chunk
                break

            # Append chunk to list, decrease size
            bufs.append(c)
            size -= len(c)
            readsize = min(size, readsize * 2)
        if readsize > self.min_readsize:
            self.min_readsize = min(readsize, self.min_readsize * 2, 512)
        return ''.join(bufs)


def open(filename, mode='rb', **kwargs):
    if isinstance(filename, (str, unicode)):
        binary_file = EncodedFile(filename, mode, **kwargs)
    elif hasattr(filename, "read") or hasattr(filename, "write"):
        binary_file = EncodedFile(None, mode, fileobj=filename, **kwargs)
    else:
        raise TypeError('filename must be a str or unicode object, or a file')
    return binary_file
