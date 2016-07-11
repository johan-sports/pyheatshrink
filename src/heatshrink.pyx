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

DEFAULT_INPUT_BUFFER_SIZE = 256


cdef class Encoder:
    cdef cheatshrink.heatshrink_encoder *_hse

    def __cinit__(self, **kwargs):
        window_sz2 = int(kwargs.get('window_sz2', DEFAULT_WINDOW_SZ2))
        lookahead_sz2 = int(kwargs.get('lookahead_sz2', DEFAULT_LOOKAHEAD_SZ2))

        if window_sz2 < MIN_WINDOW_SZ2 or window_sz2 > MAX_WINDOW_SZ2:
            msg = 'Invalid window_sz2 {}. Valid values are between {} and {}.'
            raise ValueError(msg.format(window_sz2, MIN_WINDOW_SZ2, MAX_WINDOW_SZ2))

        if lookahead_sz2 < MIN_LOOKAHEAD_SZ2 or lookahead_sz2 >= window_sz2:
            msg = 'Invalid lookahead_sz2 {}. Valid values are between {} and {}.'
            raise ValueError(msg.format(lookahead_sz2, MIN_LOOKAHEAD_SZ2, window_sz2))

        self._hse = cheatshrink.heatshrink_encoder_alloc(window_sz2, lookahead_sz2)
        if self._hse is NULL:
            raise MemoryError

    def __dealloc__(self):
        if self._hse is not NULL:
            cheatshrink.heatshrink_encoder_free(self._hse)

    @property
    def max_output_size(self):
        """The maximum allowed size of the output buffer."""
        return 1 << self._hse.window_sz2

    cdef size_t sink(self, array.array in_buf):
        """
        Sink up to `size` bytes in to the encoder.
        """
        cdef size_t input_size
        res = cheatshrink.heatshrink_encoder_sink(
            self._hse, in_buf.data.as_uchars,
            <size_t>len(in_buf), &input_size)
        if res < 0:
            raise RuntimeError("Encoder sink failed.")
        return input_size

    cdef poll(self):
        """
        Poll the output from the encoder.
        This should return an array of bytes.
        """
        cdef size_t poll_size

        cdef array.array out_buf = array.array('B', [])
        # Resize to a decent length
        array.resize(out_buf, self.max_output_size)

        # unsigned char == uint8_t guaranteed
        res = cheatshrink.heatshrink_encoder_poll(
            self._hse, out_buf.data.as_uchars,
            self.max_output_size, &poll_size)
        if res < 0:
            raise RuntimeError("Encoder poll failed.")

        # Resize to drop unused elements
        array.resize(out_buf, poll_size)

        done = res == cheatshrink.HSER_POLL_EMPTY
        return (out_buf, done)

    cdef finish(self):
        """
        Notify the encoder that the input stream is finished.
        """
        res = cheatshrink.heatshrink_encoder_finish(self._hse)
        if res < 0:
            raise RuntimeError("Encoder finish failed.")
        return res == cheatshrink.HSER_FINISH_DONE


def encode(buf, **kwargs):
    """Encode iterable `buf`."""
    encoder = Encoder(**kwargs)

    # Convert input to a byte representation
    cdef array.array byte_buf = array.array('B', buf)

    cdef int total_sunk_size = 0
    cdef array.array encoded = array.array('B', [])
    # TODO: Clean up this logic
    while True:
        if total_sunk_size < len(byte_buf):
            total_sunk_size += encoder.sink(byte_buf)

        while True:
            polled, done = encoder.poll()
            array.extend(encoded, polled)
            if done:
                break

        if total_sunk_size >= len(byte_buf):
            if encoder.finish():
                break

    # FIXME: Find a better representation for this data.
    # FIXME: memoryview vs array
    return memoryview(encoded.tostring())


# TODO: Consider using metaclasses for less duplication
cdef class Decoder:
    cdef cheatshrink.heatshrink_decoder *_hsd

    def __cinit__(self, **kwargs):
        window_sz2 = int(kwargs.get('window_sz2', DEFAULT_WINDOW_SZ2))
        lookahead_sz2 = int(kwargs.get('lookahead_sz2', DEFAULT_LOOKAHEAD_SZ2))
        input_buffer_size = int(kwargs.get('input_buffer_size', DEFAULT_INPUT_BUFFER_SIZE))

        if window_sz2 < MIN_WINDOW_SZ2 or window_sz2 > MAX_WINDOW_SZ2:
            msg = 'Invalid window_sz2 {}. Valid values are between {} and {}.'
            raise ValueError(msg.format(window_sz2, MIN_WINDOW_SZ2, MAX_WINDOW_SZ2))

        if lookahead_sz2 < MIN_LOOKAHEAD_SZ2 or lookahead_sz2 >= window_sz2:
            msg = 'Invalid lookahead_sz2 {}. Valid values are between {} and {}.'
            raise ValueError(msg.format(lookahead_sz2, MIN_LOOKAHEAD_SZ2, window_sz2))

        self._hsd = cheatshrink.heatshrink_decoder_alloc(
            window_sz2, lookahead_sz2, input_buffer_size)
        if self._hsd is NULL:
            raise MemoryError

    def __dealloc__(self):
        if self._hsd is not NULL:
            cheatshrink.heatshrink_decoder_free(self._hsd)

    @property
    def max_output_size(self):
        """The maximum allowed size of the output buffer."""
        # return 1 << self._hsd.window_sz2
        return 2048

    cdef size_t sink(self, array.array in_buf):
        """
        Sink up to `size` bytes in to the encoder.
        """
        cdef size_t input_size
        res = cheatshrink.heatshrink_decoder_sink(
            self._hsd, <uint8_t *>in_buf.buf,
            <size_t>in_buf.shape[0], &input_size)
        if res < 0:
            raise RuntimeError("Encoder sink failed.")
        return input_size

    cdef poll(self):
        """
        Poll the output from the encoder.
        This should return an array of bytes.
        """
        cdef size_t poll_size

        cdef array.array out_buf = array.array('B', [])
        # Resize to a decent length
        array.resize(out_buf, self.max_output_size)

        # unsigned char == uint8_t guaranteed
        res = cheatshrink.heatshrink_decoder_poll(
            self._hsd, out_buf.data.as_uchars,
            self.max_output_size, &poll_size)
        if res < 0:
            raise RuntimeError("Encoder poll failed.")

        # Resize to drop unused elements
        array.resize(out_buf, poll_size)

        done = res == cheatshrink.HSDR_POLL_EMPTY
        return (out_buf, done)

    cdef finish(self):
        """
        Notify the encoder that the input stream is finished.
        """
        res = cheatshrink.heatshrink_decoder_finish(self._hsd)
        if res < 0:
            raise RuntimeError("Encoder finish failed.")
        return res == cheatshrink.HSDR_FINISH_DONE


# def decode(view, **kwargs):
#     decoder = Decoder(**kwargs)

#     cdef int total_sunk_size = 0
#     cdef array.array decoded = array.array('B', [])
#     while True:
#         if total_sunk_size < view.shape[0]:
#             total_sunk_size += decoder.sink(view)

#         while True:
#             polled, done = decoder.poll()
#             array.extend(decoded, polled)
#             if done:
#                 break

#         if total_sunk_size >= view.shape[0]:
#             if decoder.finish():
#                 break

#     # FIXME: Find a better representation for this data.
#     # FIXME: Considerations include: memoryview, array
#     return decoded.tostring()
