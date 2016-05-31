/* FIXME: This isn't cross platform */
#include <Python.h>

#include <heatshrink/heatshrink_encoder.h>
#include <heatshrink/heatshrink_decoder.h>

#include "dynamic_arrays.h"

/* Redefine heatshrink debug logs according to NDEBUG. */
#undef HEATSHRINK_DEBUGGING_LOGS
#ifdef NDEBUG
#define HEATSHRINK_DEBUGGING_LOGS 0

#define log_debug(msg, ...) ((void) 0) /* Do nothing */
#else
#define HEATSHRINK_DEBUGGING_LOGS 1

#define log_debug(msg, ...)																							\
		fprintf(stdout, "[DEBUG] (%s:%d) " msg "\n", __FILE__, __LINE__, ##__VA_ARGS__)
#endif /* NDEBUG */

#define DEFAULT_HEATSHRINK_WINDOW_SZ2 11
#define DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2 4
#define DEFAULT_DECODER_INPUT_BUFFER_SIZE 256

/************************************************************
 * Encoding
 ************************************************************/
typedef enum {
		PyHSE_OK,
		PyHSE_FAILED_SINK=-1,
		PyHSE_FAILED_POLL=-2,
		PyHSE_FAILED_FINISH=-3,
} PyHS_encode_res;


static PyHS_encode_res
encode_to_array(heatshrink_encoder *hse, uint8_t *in_buf, size_t in_size,
								UInt8Array *out_arr)
{
		HSE_sink_res sink_res;
		HSE_poll_res poll_res;
		HSE_finish_res finish_res;
		size_t total_sunk_size = 0;

		size_t out_size = 1 << hse->window_sz2;
		uint8_t out_buf[out_size];
		while(1) {
				size_t sunk_size;
				size_t poll_size;

				/* Sink */
				if(total_sunk_size < in_size) {
						sink_res = heatshrink_encoder_sink(hse,
																							 &in_buf[total_sunk_size],
																							 in_size - total_sunk_size,
																							 &sunk_size);
						if(sink_res < 0) {
								return PyHSE_FAILED_SINK;
						}
						total_sunk_size += sunk_size;
				}

				do
				{
						/* Poll input result */
						poll_res = heatshrink_encoder_poll(hse, out_buf, out_size, &poll_size);
						if(poll_res < 0) {
								return PyHSE_FAILED_POLL;
						}
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
								log_debug("encoder finish failed");
								return PyHSE_FAILED_FINISH;
						}
				}
		}

		return PyHSE_OK;
}

static Py_buffer *
array_to_buffer(const UInt8Array *arr)
{
		Py_buffer *view = (Py_buffer *) malloc(sizeof(Py_buffer));
		view->obj = NULL;
		view->buf = uint8_array_copy(arr); /* Transfer ownership to Py_buffer */
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
PyHS_encode(PyObject *self, PyObject *args)
{
		unsigned char *in_buf = NULL;
		int in_size;
		/* static_cast(char * => unsigned char *) */
		if(!PyArg_ParseTuple(args, "t#", &in_buf, &in_size))
				return NULL;

		heatshrink_encoder *hse = heatshrink_encoder_alloc(
				DEFAULT_HEATSHRINK_WINDOW_SZ2,
				DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2);
		if(hse == NULL) {
				PyErr_SetString(PyExc_MemoryError, "Failed to allocate encoder");
				return NULL;
		}

		/* Initialize output buffer */
		UInt8Array *out_arr = uint8_array_create(1 << hse->window_sz2);
		/* We can safely cast them as unsigned char and uint8 always
			 have the same size. See this: http://stackoverflow.com/a/1725867 */
		PyHS_encode_res eres = encode_to_array(hse, (uint8_t *) in_buf, in_size, out_arr);

		log_debug("Wrote %zd bytes to out_arr", uint8_array_count(out_arr));
		log_debug("Capacity %zd bytes of out_arr", uint8_array_capacity(out_arr));

		PyObject *ret;
		switch(eres) {
		case PyHSE_FAILED_SINK: {
				PyErr_SetString(PyExc_RuntimeError, "Encoder sink failed.");
				ret = NULL;
				break;
		}
		case PyHSE_FAILED_POLL: {
				PyErr_SetString(PyExc_RuntimeError, "Encoder poll failed.");
				ret = NULL;
				break;
		}
		case PyHSE_FAILED_FINISH: {
				PyErr_SetString(PyExc_RuntimeError, "Encoder finish failed.");
				ret = NULL;
				break;
		}
		default: {
				Py_buffer *view = array_to_buffer(out_arr);
				ret = PyMemoryView_FromBuffer(view);
				break;
		}
		}

		/* De-allocate resources */
		heatshrink_encoder_free(hse);
		uint8_array_free(out_arr);

		return ret;
}

/************************************************************
 * Decoding
 ************************************************************/
typedef enum {
		PyHSD_OK,
		PyHSD_FAILED_SINK=-1,
		PyHSD_FAILED_POLL=-2,
		PyHSD_FAILED_FINISH=-3,
} PyHS_decode_res;

static PyHS_decode_res
decode_to_array(heatshrink_decoder *hsd, uint8_t *in_buf, size_t in_size,
								UInt8Array *out_arr)
{
		HSD_sink_res sink_res;
		HSD_poll_res poll_res;
		HSD_finish_res finish_res;
		size_t total_sunk_size = 0;

		size_t out_size = 1 << hsd->window_sz2;
		uint8_t out_buf[out_size];
		while(1) {
				size_t sunk_size;
				size_t poll_size;

				/* Sink */
				if(total_sunk_size < in_size) {
						sink_res = heatshrink_decoder_sink(hsd,
																							 &in_buf[total_sunk_size],
																							 in_size - total_sunk_size,
																							 &sunk_size);
						if(sink_res < 0) {
								return PyHSD_FAILED_SINK;
						}
						total_sunk_size += sunk_size;
				}

				do
				{
						/* Poll input result */
						poll_res = heatshrink_decoder_poll(hsd, out_buf, out_size, &poll_size);
						if(poll_res < 0) {
								return PyHSD_FAILED_POLL;
						}
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
								log_debug("decoder finish failed");
								return PyHSD_FAILED_FINISH;
						}
				}
		}

		return PyHSD_OK;
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
#define THROW_AND_EXIT(error_type, msg) {			\
				PyErr_SetString((error_type), (msg)); \
				PyBuffer_Release(&view);							\
				return NULL;													\
		}

		/* Validate dimensions */
		if(view.ndim != 1)
				THROW_AND_EXIT(PyExc_TypeError, "Expected a 1-dimensional array");

		/* Validate array item type */
		if(strcmp(view.format, "B") != 0)
				THROW_AND_EXIT(PyExc_TypeError, "Expected an array of unsigned bytes");

		log_debug("Received buffer of size %zd", view.shape[0]);

		heatshrink_decoder *hsd = heatshrink_decoder_alloc(
				DEFAULT_DECODER_INPUT_BUFFER_SIZE,
				DEFAULT_HEATSHRINK_WINDOW_SZ2,
				DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2);
		if(hsd == NULL)
				THROW_AND_EXIT(PyExc_MemoryError, "Failed to allocate decoder");

		UInt8Array *out_arr = uint8_array_create(1 << hsd->window_sz2);
		PyHS_decode_res dres = decode_to_array(hsd, (uint8_t *) view.buf,
																					 view.shape[0], out_arr);

		log_debug("Wrote %zd bytes to out_arr", uint8_array_count(out_arr));
		log_debug("Capacity %zd bytes of out_arr", uint8_array_capacity(out_arr));

		PyObject *ret;
		switch(dres) {
		case PyHSD_FAILED_SINK: {
				PyErr_SetString(PyExc_RuntimeError, "Decoder sink failed.");
				ret = NULL;
				break;
		}
		case PyHSD_FAILED_POLL: {
				PyErr_SetString(PyExc_RuntimeError, "Decoder poll failed.");
				ret = NULL;
				break;
		}
		case PyHSD_FAILED_FINISH: {
				PyErr_SetString(PyExc_RuntimeError, "Decoder finish failed.");
				ret = NULL;
				break;
		}
		default: {
				ret = PyString_FromStringAndSize((char *) uint8_array_raw(out_arr),
																				 (Py_ssize_t) uint8_array_count(out_arr));
				break;
		}
		}

		/* Indicate that we're done with the buffer */
		PyBuffer_Release(&view);
		/* De-allocate resources */
		heatshrink_decoder_free(hsd);
		uint8_array_free(out_arr);

		return ret;
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
