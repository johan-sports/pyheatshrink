cimport cheatshrink

DEFAULT_WINDOW_SZ2 = 11
DEFAULT_LOOKAHEAD_SZ2 = 4

cdef class Encoder:
    cdef cheatshrink.heatshrink_encoder* _hse

    def __cinit__(self, **kwargs):
        self._hse = cheatshrink.heatshrink_encoder_alloc(
            kwargs.get('window_sz2', DEFAULT_WINDOW_SZ2),
            kwargs.get('lookahead_sz2', DEFAULT_LOOKAHEAD_SZ2))
        if self._hse is NULL:
            raise MemoryError()

    def __dealloc__(self):
        if self._hse is not NULL:
            cheatshrink.heatshrink_encoder_free(self._hse)

    def sink(self, in_buf):
		pass

    def poll(self, out_buf):
	    pass

    def finish(self):
	    pass


def encode(buf, window_sz2=11, lookahead_sz2=4):
    encoder = Encoder()

def decode(buf, window_sz2=11, lookahead_sz2=4):
    pass
