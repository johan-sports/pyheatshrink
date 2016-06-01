#include "dynamic_arrays.h"

#include <string.h>

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
    arr->end = 0;
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
    arr->end = 0;
}

void
uint8_array_insert(UInt8Array *arr, const uint8_t *vals, size_t vals_size)
{
    if(vals == NULL || vals_size == 0)
        return;

    /* Can we fit the new values without resizing? */
    if(vals_size + arr->end <= arr->capacity) {
        memcpy(arr->data + arr->end, vals, vals_size * sizeof(uint8_t));
        arr->end += vals_size;
    } else {
        size_t new_size = arr->capacity + vals_size;
        uint8_t *new_array = (uint8_t *) malloc(new_size);
        /* Copy current data */
        memcpy(new_array, arr->data, arr->end * sizeof(uint8_t));
        /* Copy new data */
        memcpy(new_array + arr->end, vals, vals_size * sizeof(uint8_t));
        free(arr->data);
        arr->data = new_array;
        arr->capacity = new_size;
        arr->end += vals_size;
    }
}

uint8_t *
uint8_array_copy(const UInt8Array *arr)
{
    size_t size = uint8_array_count(arr);
    uint8_t *copy = calloc(size, sizeof(uint8_t));
    if(copy == NULL)
        return NULL;
    memcpy(copy, uint8_array_raw(arr), size * sizeof(uint8_t));
    return copy;
}
