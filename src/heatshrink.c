/* FIXME: This isn't cross platform */
#include <Python/Python.h>

/* FIXME: Add to include path */
#include "../heatshrink/heatshrink_encoder.h"
#include "../heatshrink/heatshrink_decoder.h"

#include "dynamic_arrays.h"

#define DEFAULT_HEATSHRINK_WINDOW_SZ2 8
#define DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2 7



/************************************************************
 * Encoding
 ************************************************************/
typedef enum {
		PYHS_OK,
		PYHS_FAILED_SINK=-1,
		PYHS_FAILED_POLL=-2,
		PYHS_FAILED_FINISH=-3,
} PyHS_encode_res;

static PyHS_encode_res
_encode_to_out(heatshrink_encoder *hse,
							 uint8_t *in_buf, size_t in_size,
							 uint8_t *out_buf, size_t out_size,
							 size_t *total_sunk)
{
		*total_sunk = -1;

		HSE_sink_res sink_res;
		HSE_poll_res poll_res;
		HSE_finish_res finish_res;
		size_t total_sunk_size = 0;
		do {
				size_t sunk_size;
				size_t poll_size;

				if(in_size > 0) {
						sink_res = heatshrink_encoder_sink(hse,
																							 &in_buf[total_sunk_size],
																							 in_size - total_sunk_size,
																							 &sunk_size);
						if(sink_res < 0) {
								return PYHS_FAILED_SINK;
						}
						total_sunk_size += sunk_size;
				}

				/* Poll input result */
				do
				{
						poll_res = heatshrink_encoder_poll(hse, out_buf, out_size, &poll_size);
						if(poll_res < 0) {
								return PYHS_FAILED_POLL;
						}
				} while(poll_res == HSER_POLL_MORE);

				if(poll_size == 0 && in_size == 0) {
						finish_res = heatshrink_encoder_finish(hse);
						if(finish_res < 0) {
								return PYHS_FAILED_FINISH;
						}
						if(finish_res == HSER_FINISH_DONE)
								break;
				}
		} while(total_sunk_size < in_size);

		*total_sunk = total_sunk_size;

		return PYHS_OK;
}

static PyObject *
PyHS_encode(PyObject *self, PyObject *args)
{
		char *in_buf = NULL;
		int in_size;
		if(!PyArg_ParseTuple(args, "t#", &in_buf, &in_size))
				return NULL;

		heatshrink_encoder *hse = heatshrink_encoder_alloc(
				DEFAULT_HEATSHRINK_WINDOW_SZ2,
				DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2);
		if(hse == NULL) {
				PyErr_SetString(PyExc_MemoryError, "failed to allocate encoder");
				return NULL;
		}

		/* Initialize output buffer */
		size_t out_size = 4096;
		uint8_t out_buf[out_size];
		memset(out_buf, 0, out_size);

		size_t total_sunk_size;
		PyHS_encode_res eres = _encode_to_out(hse, in_buf, in_size,
																					out_buf, out_size,
																					&total_sunk_size);

		heatshrink_encoder_free(hse);

		switch(eres) {
		case PYHS_FAILED_SINK:
				PyErr_SetString(PyExc_RuntimeError, "encoder sink failed");
				return NULL;
		case PYHS_FAILED_POLL:
				PyErr_SetString(PyExc_RuntimeError, "encoder poll failed");
				return NULL;
		case PYHS_FAILED_FINISH:
				PyErr_SetString(PyExc_RuntimeError, "encoder finish failed");
				return NULL;
		default:
				return PyInt_FromSize_t(total_sunk_size);
		}
}

/************************************************************
 * TODO: Decoder
 ************************************************************/

static PyObject *
PyHS_decode(PyObject *self, PyObject *args)
{
		PyErr_SetString(PyExc_NotImplementedError, "not implemented");
		return NULL;
}

/************************************************************
 * Module definition
 ************************************************************/
static PyMethodDef Heatshrink_methods [] = {
		{"encode", PyHS_encode, METH_VARARGS,
		 "Encode buffer."},
		{"decode", PyHS_decode, METH_VARARGS,
		 "Decode buffer."},
		{NULL, NULL, 0, NULL} // Sentinel
};

/************************************************************
 * Initialization
 ************************************************************/
#ifndef PyMODINIT_FUNC	/* declarations for DLL import/export */
#define PyMODINIT_FUNC void
#endif

PyMODINIT_FUNC
initheatshrink(void)
{
		(void) Py_InitModule("heatshrink", Heatshrink_methods);
}
