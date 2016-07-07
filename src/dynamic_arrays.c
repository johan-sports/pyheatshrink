#include "dynamic_arrays.h"

#include <string.h>

const float GROWTH_RATE = 2.0;

UInt8Array *
uint8_array_create(size_t initial_size)
{
    UInt8Array *arr = malloc(sizeof(*arr));
    if(arr == NULL)
        return NULL;

    arr->data = calloc(initial_size, sizeof(uint8_t));
    if(arr->data == NULL)
        return NULL;

    arr->capacity = initial_size;
    arr->count = 0;
    return arr;
}

void
uint8_array_free(UInt8Array *arr)
{
    if(arr != NULL) {
        if(arr->data != NULL) {
            free(arr->data);
            arr->data = NULL;
        }
        free(arr);
    }
}

void
uint8_array_clear(UInt8Array *arr)
{
    arr->count = 0;
}

void
uint8_array_insert(UInt8Array *arr, const uint8_t *vals, size_t vals_size)
{
    if(vals == NULL || vals_size == 0)
        return;

    /* Can we fit the new values without resizing? */
    if(vals_size + arr->count <= arr->capacity) {
        memcpy(arr->data + arr->count, vals, vals_size * sizeof(uint8_t));
        arr->count += vals_size;
    } else {
        /* Resize strategy attempts to resize the array by 2. If the new
           data still exceeds this, try and resize again. */
        size_t new_size = arr->capacity * GROWTH_RATE;
        while(new_size < arr->capacity + vals_size) {
            new_size *= GROWTH_RATE;
        }

        arr->data = realloc(arr->data, new_size * sizeof(uint8_t));
        arr->capacity = new_size;
				/* Insert new data */
				uint8_array_insert(arr, vals, vals_size);
    }
}

uint8_t *
uint8_array_copy(const UInt8Array *arr)
{
		uint8_t *copy = malloc(arr->count * sizeof(uint8_t));
    if(copy == NULL)
        return NULL;

    memcpy(copy, arr->data, arr->count * sizeof(uint8_t));

		return copy;
}
