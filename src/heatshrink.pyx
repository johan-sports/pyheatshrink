cimport cheatshrink

def encode(buf, window_sz2=11, lookahead_sz2=4):
    hse = cheatshrink.heatshrink_encoder_alloc(window_sz2, lookahead_sz2)
    if not hse:
        raise MemoryError("Failed to allocate encoder.")

    total_sunk_size = 0
    out_buf = []

    # while True:
    #     cdef size_t sunk_size
    #     cdef size_t poll_size

    #     if total_sunk_size < len(buf):
    #         sink_res = cheatshrink.heatshrink_encoder_sink(hse)

    cheatshrink.heatshrink_encoder_free(hse)

def decode(buf, window_sz2=11, lookahead_sz2=4):
    print('Decode')
