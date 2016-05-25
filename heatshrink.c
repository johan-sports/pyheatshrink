#include <Python/Python.h>

#include "heatshrink/heatshrink_encoder.h"
#include "heatshrink/heatshrink_decoder.h"

// const uint8_t DEFAULT_HEATSHRINK_WINDOW_SZ2 = 8;
// const uint8_t DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2 = 7;

static PyMethodDef HeatshrinkMethods [] = {
    {NULL, NULL, 0, NULL} // Sentinel
};

/************************************************************
 * Initialization
 ************************************************************/
#if (PY_MAJOR_VERSION >= 3)
static struct PyModuleDef HeatshrinkModule = {
    PyModuleDef_HEAD_INIT,
    "heatshrink",
    NULL,
    -1,
    HeatshrinkMethods,
    NULL,
    NULL,
    NULL,
    NULL
};

PyMODINIT_FUNC
PyInit_heatshrink(void)
{
		return PyModule_Create(&HeatshrinkModule);
}

#else /* Python 2 */
PyMODINIT_FUNC
initheatshrink(void)
{
    (void) Py_InitModule("heatshrink", HeatshrinkMethods);
}
#endif
