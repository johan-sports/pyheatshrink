import array
import numbers
cimport cython
from cpython cimport array
from libc.stdint cimport uint8_t

cimport _heatshrink


MIN_WINDOW_SZ2 = _heatshrink.HEATSHRINK_MIN_WINDOW_BITS
MAX_WINDOW_SZ2 = _heatshrink.HEATSHRINK_MAX_WINDOW_BITS
DEFAULT_WINDOW_SZ2 = 11

MIN_LOOKAHEAD_SZ2 = _heatshrink.HEATSHRINK_MIN_LOOKAHEAD_BITS
DEFAULT_LOOKAHEAD_SZ2 = 4

DEFAULT_INPUT_BUFFER_SIZE = 2048


def _validate_bounds(val, name, min=None, max=None):
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


cdef class _Writer:
    """Thin wrapper around heatshrink_encoder"""
    cdef _heatshrink.heatshrink_encoder *_hse

    def __cinit__(self, window_sz2, lookahead_sz2):
        _validate_bounds(window_sz2, name='window_sz2',
                        min=MIN_WINDOW_SZ2, max=MAX_WINDOW_SZ2)
        _validate_bounds(lookahead_sz2, name='lookahead_sz2',
                        min=MIN_LOOKAHEAD_SZ2, max=window_sz2)

        self._hse = _heatshrink.heatshrink_encoder_alloc(window_sz2, lookahead_sz2)
        if self._hse is NULL:
            raise MemoryError()

    def __dealloc__(self):
        if self._hse is not NULL:
            _heatshrink.heatshrink_encoder_free(self._hse)

    cpdef sink(self, uint8_t *in_buf, size_t size):
        cdef size_t sink_size
        res = _heatshrink.heatshrink_encoder_sink(self._hse, in_buf, size, &sink_size)
        return res, sink_size

    @property
    def max_output_size(self):
        return 1 << self._hse.window_sz2

    cpdef poll(self, uint8_t *out_buf, size_t out_buf_size):
        cdef size_t poll_size
        res = _heatshrink.heatshrink_encoder_poll(self._hse, out_buf, out_buf_size, &poll_size)
        return res, poll_size

    def is_poll_empty(self, res):
        return res == _heatshrink.HSER_POLL_EMPTY

    def finish(self):
        return _heatshrink.heatshrink_encoder_finish(self._hse)

    def is_finished(self, res):
        return res == _heatshrink.HSER_FINISH_DONE


cdef class _Reader:
    """Thin wrapper around heatshrink_decoder"""
    cdef _heatshrink.heatshrink_decoder *_hsd

    def __cinit__(self, input_buffer_size, window_sz2, lookahead_sz2):
        _validate_bounds(input_buffer_size, name='input_buffer_size', min=0)
        _validate_bounds(window_sz2, name='window_sz2',
                        min=MIN_WINDOW_SZ2, max=MAX_WINDOW_SZ2)
        _validate_bounds(lookahead_sz2, name='lookahead_sz2',
                        min=MIN_LOOKAHEAD_SZ2, max=window_sz2)

        self._hsd = _heatshrink.heatshrink_decoder_alloc(
                        input_buffer_size, window_sz2, lookahead_sz2)
        if self._hsd is NULL:
            raise MemoryError()

    def __dealloc__(self):
        if self._hsd is not NULL:
            _heatshrink.heatshrink_decoder_free(self._hsd)

    cpdef sink(self, uint8_t *in_buf, size_t size):
        cdef size_t sink_size
        res = _heatshrink.heatshrink_decoder_sink(self._hsd, in_buf, size, &sink_size)
        return res, sink_size

    @property
    def max_output_size(self):
        return 1 << self._hsd.window_sz2

    cpdef poll(self, uint8_t *out_buf, size_t out_buf_size):
        cdef size_t poll_size
        res = _heatshrink.heatshrink_decoder_poll(self._hsd, out_buf, out_buf_size, &poll_size)
        return res, poll_size

    def is_poll_empty(self, res):
        return res == _heatshrink.HSDR_POLL_EMPTY

    def finish(self):
        return _heatshrink.heatshrink_decoder_finish(self._hsd)

    def is_finished(self, res):
        return res == _heatshrink.HSDR_FINISH_DONE


# TODO: Use a better name
class Encoder(object):
    def __init__(self, encoder):
        self._encoder = encoder

    def _drain(self):
        """Empty data from the encoder state machine."""
        cdef size_t poll_size
        cdef array.array polled = array.array('B', [])
        # Resize to a decent length
        array.resize(polled, self._encoder.max_output_size)

        while True:
            res, poll_size = self._encoder.poll(polled.data.as_uchars, len(polled))

            if res < 0:
                raise RuntimeError('Encoder polling failed.')

            # Resize to drop unused elements
            array.resize(polled, poll_size)
            yield polled

            if self._encoder.is_poll_empty(res):
                raise StopIteration

    def fill(self, buf):
        """
        Fill the encoder state machine with a buffer.
        """
        if isinstance(buf, (unicode, memoryview)):
            msg = "Cannot fill encoder with type '{.__name__}'"
            raise TypeError(msg.format(buf.__class__))

        # Convert input to a byte representation
        cdef array.array in_buf  = array.array('B', buf)
        cdef array.array out_buf = array.array('B', [])

        cdef size_t sink_size = 0
        cdef size_t total_sunk_size = 0

        while total_sunk_size < len(in_buf):
            res, sink_size = self._encoder.sink(&in_buf.data.as_uchars[total_sunk_size],
                                                len(in_buf) - total_sunk_size)

            if res < 0:
                raise RuntimeError('Encoder sink failed.')

            # Clear state machine
            for data in self._drain():
                out_buf.extend(data)

            total_sunk_size += sink_size

        return out_buf.tostring()

    # TODO: Find a way to handle that there may be left over
    # TODO: data in the state machine.
    def finish(self):
        cdef array.array out_buf = array.array('B', [])

        while True:
            res = self._encoder.finish()
            if res < 0:
                raise RuntimeError('Encoder finish failed.')
            elif self._encoder.is_finished(res):
                break

            for data in self._drain():
                out_buf.extend(data)

        return out_buf.tostring()


cdef encode_impl(encoder, buf):
    """Encode iterable `buf` into an array of bytes."""
    encoder = Encoder(encoder)

    encoded = encoder.fill(buf)
    # Add any extra data remaining in the state machine
    encoded += encoder.finish()

    return encoded


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

    encoder = _Writer(encode_params['window_sz2'],
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
    decode_params = {
        'input_buffer_size': DEFAULT_INPUT_BUFFER_SIZE,
        'window_sz2': DEFAULT_WINDOW_SZ2,
        'lookahead_sz2': DEFAULT_LOOKAHEAD_SZ2,
    }
    decode_params.update(kwargs)

    encoder = _Reader(decode_params['input_buffer_size'],
                      decode_params['window_sz2'],
                      decode_params['lookahead_sz2'])
    return encode_impl(encoder, buf)


def sink_p(e, array.array data, offset):
    return e.sink(&data.data.as_uchars[offset], len(data) - offset)

def poll_p(e, array.array data, data_sz):
    array.resize(data, data_sz)
    res, poll_sz = e.poll(data.data.as_uchars, len(data))
    array.resize(data, poll_sz)
    return res, poll_sz
