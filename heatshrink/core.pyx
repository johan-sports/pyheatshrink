import array
import numbers
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


cdef class Writer:
    """Thin wrapper around heatshrink_encoder"""
    cdef _heatshrink.heatshrink_encoder *_hse

    def __cinit__(self, **kwargs):
        window_sz2 = kwargs.get('window_sz2', DEFAULT_WINDOW_SZ2)
        lookahead_sz2 = kwargs.get('lookahead_sz2', DEFAULT_LOOKAHEAD_SZ2)

        _validate_bounds(window_sz2, name='window_sz2',
                         min=MIN_WINDOW_SZ2, max=MAX_WINDOW_SZ2)
        _validate_bounds(lookahead_sz2, name='lookahead_sz2',
                         min=MIN_LOOKAHEAD_SZ2, max=window_sz2)

        self._hse = _heatshrink.heatshrink_encoder_alloc(window_sz2, lookahead_sz2)
        if self._hse is NULL:
            raise MemoryError('Failed to allocate encoder.')

    def __dealloc__(self):
        if self._hse is not NULL:
            _heatshrink.heatshrink_encoder_free(self._hse)

    @property
    def max_output_size(self):
        return 1 << self._hse.window_sz2

    def sink(self, array.array in_buf, size_t offset=0):
        """
        Sink input in to the encoder with an optional N byte `offset`.
        """
        cdef:
            size_t sink_size
            _heatshrink.HSE_sink_res res

            size_t in_buf_size = len(in_buf)

        res = _heatshrink.heatshrink_encoder_sink(
            self._hse,
            &in_buf.data.as_uchars[offset],
            in_buf_size - offset,
            &sink_size
        )
        return res, sink_size

    def poll(self, array.array out_buf):
        """Poll data from state machine in to an array.

        Assumes that the passed in array is large enough to
        contain all data from the state machine.
        """
        cdef:
            size_t poll_size
            _heatshrink.HSE_poll_res res

            size_t out_buf_size = len(out_buf)

        res = _heatshrink.heatshrink_encoder_poll(
            self._hse,
            out_buf.data.as_uchars,
            out_buf_size,
            &poll_size
        )
        return res, poll_size

    def is_poll_empty(self, _heatshrink.HSE_poll_res res):
        return res == _heatshrink.HSER_POLL_EMPTY

    def finish(self):
        """Notifies the encoder that the input stream is finished."""
        return _heatshrink.heatshrink_encoder_finish(self._hse)

    def is_finished(self, _heatshrink.HSE_finish_res res):
        return res == _heatshrink.HSER_FINISH_DONE


cdef class Reader:
    """Thin wrapper around heatshrink_decoder"""
    cdef _heatshrink.heatshrink_decoder *_hsd

    def __cinit__(self, **kwargs):
        input_buffer_size = kwargs.get('input_buffer_size',
                                       DEFAULT_INPUT_BUFFER_SIZE)
        window_sz2 = kwargs.get('window_sz2', DEFAULT_WINDOW_SZ2)
        lookahead_sz2 = kwargs.get('lookahead_sz2', DEFAULT_LOOKAHEAD_SZ2)

        _validate_bounds(input_buffer_size, name='input_buffer_size', min=0)
        _validate_bounds(window_sz2, name='window_sz2',
                         min=MIN_WINDOW_SZ2, max=MAX_WINDOW_SZ2)
        _validate_bounds(lookahead_sz2, name='lookahead_sz2',
                         min=MIN_LOOKAHEAD_SZ2, max=window_sz2)

        self._hsd = _heatshrink.heatshrink_decoder_alloc(
            input_buffer_size, window_sz2, lookahead_sz2)
        if self._hsd is NULL:
            raise MemoryError('Failed to allocate decoder.')

    def __dealloc__(self):
        if self._hsd is not NULL:
            _heatshrink.heatshrink_decoder_free(self._hsd)

    @property
    def max_output_size(self):
        return 1 << self._hsd.window_sz2

    def sink(self, array.array in_buf, size_t offset=0):
        """
        Sink input in to the encoder with an optional N byte `offset`.
        """
        cdef:
            size_t sink_size
            _heatshrink.HSD_sink_res res

            size_t in_buf_size = len(in_buf)

        res = _heatshrink.heatshrink_decoder_sink(
            self._hsd,
            &in_buf.data.as_uchars[offset],
            in_buf_size - offset,
            &sink_size
        )
        return res, sink_size

    def poll(self, array.array out_buf):
        cdef:
            size_t poll_size
            _heatshrink.HSD_poll_res res

            size_t out_buf_size = len(out_buf)

        res = _heatshrink.heatshrink_decoder_poll(
            self._hsd,
            out_buf.data.as_uchars,
            out_buf_size,
            &poll_size
        )
        return res, poll_size

    def is_poll_empty(self, _heatshrink.HSD_poll_res res):
        return res == _heatshrink.HSDR_POLL_EMPTY

    def finish(self):
        """Notifies the encoder that the input stream is finished."""
        return _heatshrink.heatshrink_decoder_finish(self._hsd)

    def is_finished(self, _heatshrink.HSD_finish_res res):
        return res == _heatshrink.HSDR_FINISH_DONE


class Encoder(object):
    """High level interface to the Heatshrink encoders/decoders."""
    def __init__(self, encoder):
        self._encoder = encoder
        self._finished = False

    def _check_not_finished(self):
        """Throws an exception if the encoder has been closed."""
        if self._finished:
            msg = 'Attempted to perform operation on a closed encoder.'
            # TODO: ValueError isn't the right exception for this
            raise ValueError(msg)

    def _drain(self):
        """Empty data from the encoder state machine."""
        cdef:
            array.array out_buf = array.array('B', [])

        while True:
            # Resize to decent length
            array.resize(out_buf, self._encoder.max_output_size)

            res, poll_size = self._encoder.poll(out_buf)
            if res < 0:
                raise RuntimeError('Encoder poll failed.')

            # Drop unused elements
            array.resize(out_buf, poll_size)

            yield out_buf

            # Done polling
            if self._encoder.is_poll_empty(res):
                raise StopIteration

    def fill(self, buf):
        """Fill the encoder state machine with a buffer."""
        self._check_not_finished()

        if isinstance(buf, (unicode, memoryview)):
            msg = "Cannot fill encoder with type '{.__name__}'"
            raise TypeError(msg.format(buf.__class__))

        # Convert input to a byte representation
        cdef array.array in_buf  = array.array('B', buf)
        cdef array.array out_buf = array.array('B', [])

        cdef size_t total_sunk = 0

        while total_sunk < len(in_buf):
            res, sunk = self._encoder.sink(in_buf, offset=total_sunk)

            if res < 0:
                raise RuntimeError('Encoder sink failed.')

            total_sunk += sunk

            # Clear state machine
            for data in self._drain():
                out_buf.extend(data)

        try:
            # Python 3
            return out_buf.tobytes()
        except AttributeError:
            return out_buf.tostring()

    def finish(self):
        """Close encoder and return any remaining data.

        Will throw an exception if fill() or finish()
        is used after this.
        """
        self._check_not_finished()

        cdef array.array out_buf = array.array('B', [])

        while True:
            res = self._encoder.finish()
            if res < 0:
                raise RuntimeError('Encoder finish failed.')

            if self._encoder.is_finished(res):
                self._finished = True
                break

            for data in self._drain():
                out_buf.extend(data)

        try:
            # Python 3
            return out_buf.tobytes()
        except AttributeError:
            return out_buf.tostring()

    @property
    def finished(self):
        """Returns true if the encoder has been closed."""
        return self._finished


cdef _encode_impl(encoder, buf):
    """Encode iterable `buf` into an array of bytes."""
    encoder = Encoder(encoder)
    return encoder.fill(buf) + encoder.finish()


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
    return _encode_impl(Writer(**kwargs), buf)


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
    return _encode_impl(Reader(**kwargs), buf)

