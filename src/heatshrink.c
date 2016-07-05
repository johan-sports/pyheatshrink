#include <Python.h>

#include <heatshrink/heatshrink_encoder.h>
#include <heatshrink/heatshrink_decoder.h>

#include "common.h"
#include "dynamic_arrays.h"

#define DEFAULT_HEATSHRINK_WINDOW_SZ2 11
#define DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2 4
#define DEFAULT_DECODER_INPUT_BUFFER_SIZE 256

/************************************************************
 * Encoding
 ************************************************************/
static UInt8Array *
encode_to_array(heatshrink_encoder *hse, uint8_t *in_buf, size_t in_size)
{
    HSE_sink_res sink_res;
    HSE_poll_res poll_res;
    HSE_finish_res finish_res;
    size_t total_sunk_size = 0;

    size_t out_size = 1 << hse->window_sz2;
    UInt8Array *out_arr = uint8_array_create(out_size);
		if(out_arr == NULL) {
				PyErr_SetString(PyExc_MemoryError, "Failed to allocate output buffer.");
				return NULL;
		}
    uint8_t out_buf[out_size];

#define THROW_AND_EXIT(exc, msg) { \
        PyErr_SetString(exc, msg); \
        uint8_array_free(out_arr); \
        return NULL;               \
    }

    while(1) {
        size_t sunk_size;
        size_t poll_size;

        /* Sink */
        if(total_sunk_size < in_size) {
            sink_res = heatshrink_encoder_sink(hse,
                                               &in_buf[total_sunk_size],
                                               in_size - total_sunk_size,
                                               &sunk_size);
            if(sink_res < 0)
                THROW_AND_EXIT(PyExc_RuntimeError, "Encoder sink failed.")

            total_sunk_size += sunk_size;
        }

        do
        {
            /* Poll input result */
            poll_res = heatshrink_encoder_poll(hse, out_buf, out_size, &poll_size);
            if(poll_res < 0)
                THROW_AND_EXIT(PyExc_RuntimeError, "Encoder poll failed.")

            uint8_array_insert(out_arr, out_buf, poll_size);
        } while(poll_res == HSER_POLL_MORE);

        if(total_sunk_size >= in_size) {
            /* Ensure all input is processed */
            finish_res = heatshrink_encoder_finish(hse);
            /* We can't use a switch because we need break to refer to the while loop */
            if(finish_res == HSER_FINISH_DONE) {
                log_debug("HSER_FINISH_DONE, encoding finished");
                break;
            } else if(finish_res == HSER_FINISH_MORE) {
                log_debug("HSER_FINISH_MORE, reruning poll");
                continue;
            } else {
                THROW_AND_EXIT(PyExc_RuntimeError, "Encoder finish failed.")
            }
        }
    }

#undef THROW_AND_EXIT

    return out_arr;
}

static Py_buffer *
array_to_buffer(const UInt8Array *arr)
{
    Py_buffer *view = (Py_buffer *) malloc(sizeof(Py_buffer));
		void *buf = uint8_array_copy(arr);
		if(buf == NULL)
				return NULL;

    view->obj = NULL;
    view->buf = buf; /* Transfer ownership to Py_buffer */
    view->len = uint8_array_count(arr) * sizeof(uint8_t);
    view->itemsize = sizeof(uint8_t);
    view->readonly = 1;
    view->format = "B"; /* 8-bit unsigned char */
    view->ndim = 1;
    view->shape = (Py_ssize_t *) &uint8_array_count(arr);
    view->strides = &view->itemsize;
    view->suboffsets = NULL;
    view->internal = NULL;

    return view;
}

static PyObject *
PyHS_encode(PyObject *self, PyObject *args, PyObject *kwargs)
{
    unsigned char *in_buf;
    int in_size;
		uint8_t window_sz2 = DEFAULT_HEATSHRINK_WINDOW_SZ2;
		uint8_t lookahead_sz2 = DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2;

		static char *kwlist[] = {"buf", "window_size", "lookahead_size", NULL};
		if(!PyArg_ParseTupleAndKeywords(args, kwargs, "t#|bb", kwlist,
																		/* static_cast(char * => unsigned char *) */
																		&in_buf, &in_size,
																		&window_sz2, &lookahead_sz2)) {
				return NULL;
		}

		if((window_sz2 < HEATSHRINK_MIN_WINDOW_BITS) ||
			 (window_sz2 > HEATSHRINK_MAX_WINDOW_BITS)) {
				PyObject *exc_msg = PyString_FromFormat(
						"Invalid window size %d. Valid values are between %d and %d.",
						window_sz2, HEATSHRINK_MIN_WINDOW_BITS, HEATSHRINK_MAX_WINDOW_BITS
				);
				PyErr_SetObject(PyExc_ValueError, exc_msg);
				Py_DECREF(exc_msg);
				return NULL;
		}

		if ((lookahead_sz2 < HEATSHRINK_MIN_LOOKAHEAD_BITS) ||
				(lookahead_sz2 >= window_sz2)) {
				PyObject *exc_msg = PyString_FromFormat(
						"Invalid lookahead size %d. Valid values are between %d and %d.",
						lookahead_sz2, HEATSHRINK_MIN_LOOKAHEAD_BITS, window_sz2
				);
				PyErr_SetObject(PyExc_ValueError, exc_msg);
				Py_DECREF(exc_msg);
				return NULL;
		}

    heatshrink_encoder *hse = heatshrink_encoder_alloc(window_sz2, lookahead_sz2);
    if(hse == NULL) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate encoder.");
        return NULL;
    }

    /* We can safely cast them as unsigned char and uint8 always
       have the same size. See this: http://stackoverflow.com/a/1725867 */
    UInt8Array *out_arr = encode_to_array(hse, (uint8_t *) in_buf, in_size);
    /* We're done with the encoder. */
    heatshrink_encoder_free(hse);

    if(out_arr == NULL)
        return NULL; /* delegate error */

    log_debug("Wrote %zd bytes to out_arr", uint8_array_count(out_arr));
    log_debug("Capacity %zd bytes of out_arr", uint8_array_capacity(out_arr));

    Py_buffer *view = array_to_buffer(out_arr);
    /* De-allocate original array, as the buffer owns a copy */
    uint8_array_free(out_arr);

		if(view == NULL) {
				PyErr_SetString(PyExc_MemoryError, "Failed to allocate view buffer.");
				return NULL;
		}
    return PyMemoryView_FromBuffer(view);
}

/************************************************************
 * Decoding
 ************************************************************/
static UInt8Array *
decode_to_array(heatshrink_decoder *hsd, uint8_t *in_buf, size_t in_size)
{
    HSD_sink_res sink_res;
    HSD_poll_res poll_res;
    HSD_finish_res finish_res;
    size_t total_sunk_size = 0;

    size_t out_size = 1 << hsd->window_sz2;
    UInt8Array *out_arr = uint8_array_create(out_size);
		if(out_arr == NULL) {
				PyErr_SetString(PyExc_MemoryError, "Failed to allocate output buffer.");
				return NULL;
		}
    uint8_t out_buf[out_size];

#define THROW_AND_EXIT(exc, msg) { \
        PyErr_SetString(exc, msg); \
        uint8_array_free(out_arr); \
        return NULL;               \
    }

    while(1) {
        size_t sunk_size;
        size_t poll_size;

        /* Sink */
        if(total_sunk_size < in_size) {
            sink_res = heatshrink_decoder_sink(hsd,
                                               &in_buf[total_sunk_size],
                                               in_size - total_sunk_size,
                                               &sunk_size);
            if(sink_res < 0)
                THROW_AND_EXIT(PyExc_RuntimeError, "Decoder sink failed.")

            total_sunk_size += sunk_size;
        }

        do
        {
            /* Poll input result */
            poll_res = heatshrink_decoder_poll(hsd, out_buf, out_size, &poll_size);
            if(poll_res < 0)
                THROW_AND_EXIT(PyExc_RuntimeError, "Decoder poll failed.")

            uint8_array_insert(out_arr, out_buf, poll_size);
        } while(poll_res == HSDR_POLL_MORE);

        if(total_sunk_size >= in_size) {
            /* Ensure all input is processed */
            finish_res = heatshrink_decoder_finish(hsd);
            /* We can't use a switch because we need break to refer to the while loop */
            if(finish_res == HSDR_FINISH_DONE) {
                log_debug("HSDR_FINISH_DONE, decoder finished");
                break;
            } else if(finish_res == HSDR_FINISH_MORE) {
                log_debug("HSDR_FINISH_MORE, reruning poll");
                continue;
            } else {
                THROW_AND_EXIT(PyExc_RuntimeError, "Decoder finish failed.")
            }
        }
    }

#undef THROW_AND_EXIT

    return out_arr;
}

static PyObject *
PyHS_decode(PyObject *self, PyObject *args)
{
    PyObject *in_obj = NULL;
    if(!PyArg_ParseTuple(args, "O", &in_obj))
        return NULL;

    Py_buffer view;
    if(PyObject_GetBuffer(in_obj, &view,
                          PyBUF_ANY_CONTIGUOUS | PyBUF_FORMAT) == -1) {
        PyErr_SetString(PyExc_TypeError,
                        "Parameter must implement the buffer protocol.");
        return NULL;
    }

    /* Thow a python error and release the view buffer, returning NULL. */
#define THROW_AND_EXIT(error_type, msg) {     \
        PyErr_SetString((error_type), (msg)); \
        PyBuffer_Release(&view);              \
        return NULL;                          \
    }

    /* Validate dimensions */
    if(view.ndim != 1)
        THROW_AND_EXIT(PyExc_TypeError, "Expected a 1-dimensional buffer");

    /* Validate array item type */
    if(strcmp(view.format, "B") != 0)
        THROW_AND_EXIT(PyExc_TypeError, "Expected a buffer of format 'B'.");

    log_debug("Received buffer of size %zd", view.shape[0]);

    heatshrink_decoder *hsd = heatshrink_decoder_alloc(
        DEFAULT_DECODER_INPUT_BUFFER_SIZE,
        DEFAULT_HEATSHRINK_WINDOW_SZ2,
        DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2);
    if(hsd == NULL)
        THROW_AND_EXIT(PyExc_MemoryError, "Failed to allocate decoder");

#undef THROW_AND_EXIT

    UInt8Array *out_arr = decode_to_array(hsd, (uint8_t *) view.buf, view.shape[0]);
    heatshrink_decoder_free(hsd);
    /* Indicate that we're done with the buffer */
    PyBuffer_Release(&view);

    if(out_arr == NULL)
        return NULL; /* delegate error */

    log_debug("Wrote %zd bytes to out_arr", uint8_array_count(out_arr));
    log_debug("Capacity %zd bytes of out_arr", uint8_array_capacity(out_arr));

    uint8_array_free(out_arr);

    return PyString_FromStringAndSize((char *) uint8_array_raw(out_arr),
                                      (Py_ssize_t) uint8_array_count(out_arr));
}

/************************************************************
 * Module definition
 ************************************************************/
static PyMethodDef Heatshrink_methods [] = {
    {"encode", PyHS_encode, METH_VARARGS | METH_KEYWORDS,
     "Encode buffer."},
    {"decode", PyHS_decode, METH_VARARGS,
     "Decode buffer."},
    {NULL, NULL, 0, NULL} // Sentinel
};

/************************************************************
 * Initialization
 ************************************************************/
#if PY_MAJOR_VERSION >= 3
#define MOD_ERROR_VAL NULL
#define MOD_SUCCESS_VAL(val) val
#define MOD_INIT(name) PyMODINIT_FUNC PyInit_##name(void)
#define MOD_DEF(obj, name, doc, methods)                  \
    static struct PyModuleDef moduledef = {               \
        PyModuleDef_HEAD_INIT, name, doc, -1, methods, }; \
    obj = PyModuleDef_HEAD_INIT(&moduledef);
#else
#define MOD_ERROR_VAL
#define MOD_SUCCESS_VAL(val)
#define MOD_INIT(name) void init##name(void)
#define MOD_DEF(obj, name, doc, methods)        \
    obj = Py_InitModule3(name, methods, doc);
#endif /* PY_MAJOR_VERSION >= 3 */


MOD_INIT(heatshrink)
{
    PyObject *m;
    MOD_DEF(m, "heatshrink", "Bindings to the heatshrink compression library",
            Heatshrink_methods);

    return MOD_SUCCESS_VAL(m);
}
