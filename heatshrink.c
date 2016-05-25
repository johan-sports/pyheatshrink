#include <Python/Python.h>

#include "heatshrink/heatshrink_encoder.h"
#include "heatshrink/heatshrink_decoder.h"

// const uint8_t DEFAULT_HEATSHRINK_WINDOW_SZ2 = 8;
// const uint8_t DEFAULT_HEATSHRINK_LOOKAHEAD_SZ2 = 7;

static PyMethodDef HeatshrinkMethods [] = {
    {NULL, NULL, 0, NULL} // Sentinel
};

PyMODINIT_FUNC initheatshrink()
{
    (void) Py_InitModule("heatshrink", HeatshrinkMethods);
}
