/* FIXME: This isn't cross platform */
#include <Python/Python.h>
#include <Python/structmember.h>

#include "heatshrink/heatshrink_encoder.h"
#include "heatshrink/heatshrink_decoder.h"

const uint8_t DEFAULT_HEATSHRINK_WINDOW_SZ2 = 8;
const uint8_t DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2 = 7;

/************************************************************
 * Encoding
 ************************************************************/
typedef struct {
		PyObject_HEAD
		heatshrink_encoder *__hse;
} PyHS_Encoder;

static void
PyHS_Encoder_dealloc(PyHS_Encoder *self)
{
		heatshrink_encoder_free(self->__hse);
		printf("Encoder de-allocated..\n");
		self->ob_type->tp_free((PyObject *) self);
}

static PyObject *
PyHS_Encoder_new(PyTypeObject *type, PyObject *args, PyObject *kwargs)
{
		PyHS_Encoder *self = (PyHS_Encoder *) type->tp_alloc(type, 0);

		if(self != NULL) {
				heatshrink_encoder *hse = heatshrink_encoder_alloc(
						DEFAULT_HEATSHRINK_WINDOW_SZ2,
						DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2
				);

				if(hse == NULL) {
						Py_DECREF(self);
						PyErr_SetString(PyExc_MemoryError, "failed to allocate encoder.");
						return NULL;
				}

				self->__hse = hse;
		}

		return (PyObject *) self;
}

static int
PyHS_Encoder_init(PyHS_Encoder *self, PyObject *args, PyObject *kwargs)
{
		return 0;
}

static PyMemberDef PyHS_Encoder_members[] = {
		{NULL, 0, 0, 0, 0} /* Sentinel */
};

static PyMethodDef PyHS_Encoder_methods[] = {
		{NULL, NULL, 0, NULL} /* Sentinel */
};


static PyTypeObject PyHS_EncoderType = {
		PyObject_HEAD_INIT(NULL)
		0,                          /* ob_size */
		"heatshrink.Encoder",       /* tp_name */
		sizeof(PyHS_Encoder),       /* tp_basicsize */
		0,                          /*tp_itemsize*/
    (destructor)PyHS_Encoder_dealloc,   /*tp_dealloc*/
    0,                          /*tp_print*/
    0,                          /*tp_getattr*/
    0,                          /*tp_setattr*/
    0,                          /*tp_compare*/
    0,                          /*tp_repr*/
    0,                          /*tp_as_number*/
    0,                          /*tp_as_sequence*/
    0,                          /*tp_as_mapping*/
    0,                          /*tp_hash */
    0,                          /*tp_call*/
    0,                          /*tp_str*/
    0,                          /*tp_getattro*/
    0,                          /*tp_setattro*/
    0,                          /*tp_as_buffer*/
		Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
		"Encoder objects",           /* tp_doc */
    0,		                       /* tp_traverse */
    0,		                       /* tp_clear */
    0,		                       /* tp_richcompare */
    0,		                       /* tp_weaklistoffset */
    0,		                       /* tp_iter */
    0,		                       /* tp_iternext */
    PyHS_Encoder_methods,        /* tp_methods */
    PyHS_Encoder_members,        /* tp_members */
    0,                           /* tp_getset */
    0,                           /* tp_base */
    0,                           /* tp_dict */
    0,                           /* tp_descr_get */
    0,                           /* tp_descr_set */
    0,                           /* tp_dictoffset */
    (initproc)PyHS_Encoder_init, /* tp_init */
    0,                           /* tp_alloc */
    PyHS_Encoder_new,            /* tp_new */
};

/************************************************************
 * Module definition
 ************************************************************/
static PyMethodDef Heatshrink_methods [] = {
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
		PyObject *m;

		if(PyType_Ready(&PyHS_EncoderType) < 0)
				return;

		m = Py_InitModule("heatshrink", Heatshrink_methods);

		if(m == NULL)
				return;

		Py_INCREF(&PyHS_EncoderType);
		PyModule_AddObject(m, "Encoder", (PyObject *) &PyHS_EncoderType);
}
