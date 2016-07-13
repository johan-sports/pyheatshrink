import array
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


cdef class Writer:
    """Thin wrapper around heatshrink_encoder"""
    cdef cheatshrink.heatshrink_encoder *_hse

    def __cinit__(self, window_sz2, lookahead_sz2):
        self._hse = cheatshrink.heatshrink_encoder_alloc(window_sz2, lookahead_sz2)
        if self._hse is NULL:
            raise MemoryError('Insufficient memory.')

    def __dealloc__(self):
        if self._hse is not NULL:
            cheatshrink.heatshrink_encoder_free(self._hse)

    # Sinkable protocol
    cdef sink(self, uint8_t *in_buf, size_t size, size_t *input_size):
        return cheatshrink.heatshrink_encoder_sink(self._hse, in_buf, size, input_size)

    # Pollable protocol
    @property
    def max_output_size(self):
        return 1 << self._hse.window_sz2

    cdef poll(self, uint8_t *out_buf, size_t out_buf_size, size_t *output_size):
        return cheatshrink.heatshrink_encoder_poll(self._hse, out_buf, out_buf_size, output_size)

    cdef is_poll_empty(self, cheatshrink.HSE_poll_res res):
        return res == cheatshrink.HSER_POLL_EMPTY

    # Finishable protocol
    cdef finish(self):
        return cheatshrink.heatshrink_encoder_finish(self._hse)

    cdef is_finished(self, cheatshrink.HSE_finish_res res):
        return res == cheatshrink.HSER_FINISH_DONE


cdef class Reader:
    """Thin wrapper around heatshrink_decoder"""
    cdef cheatshrink.heatshrink_decoder *_hsd

    def __cinit__(self, input_buffer_size, window_sz2, lookahead_sz2):
        self._hsd = cheatshrink.heatshrink_decoder_alloc(
            input_buffer_size, window_sz2, lookahead_sz2)
        if self._hsd is NULL:
            raise MemoryError('Insufficient memory.')

    def __dealloc__(self):
        if self._hsd is not NULL:
            cheatshrink.heatshrink_decoder_free(self._hsd)

    cdef sink(self, uint8_t *in_buf, size_t size, size_t *input_size):
        return cheatshrink.heatshrink_decoder_sink(self._hsd, in_buf, size, input_size)

    @property
    def max_output_size(self):
        return 1 << self._hsd.window_sz2

    cdef poll(self, uint8_t *out_buf, size_t out_buf_size, size_t *output_size):
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
    Sink input in to the encoder, with an optional N byte `offset`.
    """
    cdef size_t sink_size

    res = obj.sink(&in_buf.data.as_uchars[offset],
                   len(in_buf) - offset, &sink_size)
    if res < 0:
        raise RuntimeError('Sink failed.')

    print('Sunk {} of {}'.format(sink_size, len(in_buf)))
    return sink_size


cdef poll(Encoder obj):
    """Poll output from an encoder/decoder."""
    cdef size_t poll_size

    cdef array.array out_buf = array.array('B', [])
    # Resize to a decent length
    array.resize(out_buf, obj.max_output_size)

    res = obj.poll(out_buf.data.as_uchars, len(out_buf), &poll_size)
    if res < 0:
        raise RuntimeError('Polling failed.')

    print('Polled {} of {}'.format(poll_size, len(out_buf)))
    # Resize to drop unused elements
    array.resize(out_buf, poll_size)

    done = obj.is_poll_empty(res)
    return (out_buf, done)


cdef finish(Encoder obj):
    res = obj.finish()
    if res < 0:
        raise RuntimeError("Finish failed.")
    return obj.is_finished(res)


cdef encode_impl(Encoder obj, buf):
    """
    Encode iterable `buf` into an array of byte primitives.
    """
    # HACK: Mitigate python 2 issues with value `Integer is required`
    # HACK: error messages for some types of objects.
    if isinstance(buf, unicode) or isinstance(buf, memoryview):
        msg = "cannot use {.__name__} to initialize an array with typecode 'B'"
        raise TypeError(msg.format(type(buf)))

    # Convert input to a byte representation
    cdef array.array byte_buf = array.array('B', buf)

    cdef size_t total_sunk_size = 0
    cdef array.array encoded = array.array('B', [])
    # TODO: Clean up this logic
    print('*** Running encoding loop with: %s' % obj.__class__.__name__)
    while True:
        if total_sunk_size < len(byte_buf):
            total_sunk_size += sink(obj, byte_buf, total_sunk_size)
            print('Total sunk size: %s' % total_sunk_size)

        # TODO: Make poll an iterator|generator. Run until done
        # for polled in obj.poll():
        #     encoded.extend(polled)
        while True:
            polled, done = poll(obj)
            encoded.extend(polled)
            if done:
                break

        if total_sunk_size >= len(byte_buf):
            if finish(obj):
                break

    try:
        # Python 3
        return encoded.tobytes()
    except AttributeError:
        return encoded.tostring()


def encode(buf, **kwargs):
    encode_params = {
        'window_sz2': DEFAULT_WINDOW_SZ2,
        'lookahead_sz2': DEFAULT_LOOKAHEAD_SZ2,
    }
    encode_params.update(kwargs)

    encoder = Writer(encode_params['window_sz2'],
                     encode_params['lookahead_sz2'])
    return encode_impl(encoder, buf)


def decode(buf, **kwargs):
    decoder = Reader(254, 11, 4)
    return encode_impl(decoder, buf)

def empty_array(size):
    arr = array.array('B', [])
    array.resize(arr, size)
    return arr
