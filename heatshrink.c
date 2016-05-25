#include <Python/Python.h>

static PyMethodDef HeatshrinkMethods [] = {
    {NULL, NULL, 0, NULL} // Sentinel
};

PyMODINIT_FUNC initheatshrink()
{
    (void) Py_InitModule("heatshrink", HeatshrinkMethods);
}
