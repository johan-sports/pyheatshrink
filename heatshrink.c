/* FIXME: This isn't cross platform */
#include <Python/Python.h>

#include "heatshrink/heatshrink_encoder.h"
#include "heatshrink/heatshrink_decoder.h"

#define DEFAULT_HEATSHRINK_WINDOW_SZ2 8
#define DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2 7

/************************************************************
 * Encoding
 ************************************************************/
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
								/* TODO: Throw exception */
								fprintf(stderr, "sink\n");
								exit(EXIT_FAILURE);
						}
						total_sunk_size += sunk_size;
				}

				/* Poll input result */
				do {
						poll_res = heatshrink_encoder_poll(hse, out_buf, out_size, &poll_size);
						if(poll_res < 0) {
								fprintf(stderr, "poll\n");
								exit(EXIT_FAILURE);
						}
				} while(poll_res == HSER_POLL_MORE);

				if(poll_size == 0 && in_size == 0) {
						finish_res = heatshrink_encoder_finish(hse);
						if(finish_res < 0) {
								fprintf(stderr, "finish\n");
								exit(EXIT_FAILURE);
						}
						if(finish_res == HSER_FINISH_DONE) {
								printf("Polling finished\n");
								break;
						}
				}
		} while(total_sunk_size < in_size);

		heatshrink_encoder_free(hse);

		return PyInt_FromSize_t(total_sunk_size);
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
