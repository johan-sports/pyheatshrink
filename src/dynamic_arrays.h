#ifndef _PY_HS_DYNAMIC_ARRAYS__
#define _PY_HS_DYNAMIC_ARRAYS__

#include <stdint.h>
#include "common.h"

/************************************************************
 * uint8 type array
 ************************************************************/
typedef struct UInt8Array {
    size_t capacity;
    size_t end;
    uint8_t *data;
} UInt8Array;

/**
 * Allocate memory for an array of size `initial_size`.
 *
 * @param {size_t} initial_size   The initial size of the array.
 * @returns {UInt8Array *}        The new array.
 */
UInt8Array *
uint8_array_create(size_t initial_capacity);

/**
 * De-allocate memory used for array. Handles NULL cases.
 *
 * @param {UInt8Array *} arr
 */
void
uint8_array_free(UInt8Array *arr);

/**
 * Clears all values from the array.
 *
 * @param {UInt8Array *}
 */
void
uint8_array_clear(UInt8Array *arr);

/**
 * Insert an array of values to the and of the existing array.
 *
 * @param {UInt8Array *} arr
 * @param {uint8_t} vals     The full set of values to insert in to the array.
 * @param {size_t} vals_size The size of the vals array.
 */
void
uint8_array_insert(UInt8Array *arr, const uint8_t *vals, size_t vals_size);

/**
 * Copy internal array data and return it.
 */
uint8_t *
uint8_array_copy(const UInt8Array *arr);

#define uint8_array_last(A) ((A)->data[(A)->end - 1])
#define uint8_array_first(A) ((A)->data[0])
#define uint8_array_raw(A) ((A)->data)
#define uint8_array_end(A) ((A)->end)
#define uint8_array_count(A) uint8_array_end(A)
#define uint8_array_capacity(A) ((A)->capacity)

#endif /* _PY_HS_DYNAMIC_ARRAYS__ */
