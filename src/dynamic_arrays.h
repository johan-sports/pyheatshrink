#ifndef _PY_HS_DYNAMIC_ARRAYS__
#define _PY_HS_DYNAMIC_ARRAYS__

#include <stdlib.h>

#define ARRAY_SIZE(arr) (sizeof(arr) / sizeof(arr[0]))

#define NEW(type) ((type *) malloc(sizeof(type)))

/************************************************************
 * uint8 type array
 ************************************************************/
typedef struct {
		uint8_t *items;
		size_t size;
		size_t used;
} UInt8Array;


/**
 * Allocate memory for an array of size `initial_size`.
 *
 * @param {size_t} initial_size   The initial size of the array.
 * @returns {UInt8Array *}        The new array.
 */
UInt8Array *
uint8_array_alloc(size_t initial_size);

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
 * Appends an item to the front of the array.
 *
 * @param {UInt8Array *} arr
 * @param {uint8_t} val      The value to append to the array
 * @returns {uint8_t}        The appended element
 */
uint8_t
uint8_array_push(UInt8Array *arr, uint8_t val);

/**
 * Removes and returns the last item in the array.
 *
 * @param{UInt8Array *} arr
 * @returns {uint8_t}       The removed element
 */
uint8_t
uint8_array_pop(UInt8Array *arr);

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
 * Dynamic variant of uint8_array_insert where the size of the
 * vals array is inferred.
 */
void
uint8_array_insert_dyn(UInt8Array *arr, const uint8_t *vals);

#endif /* _PY_HS_DYNAMIC_ARRAYS__ */
