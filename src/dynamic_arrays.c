#include "dynamic_arrays.h"

#include <string.h>

void
_check_array_size(UInt8Array *arr)
{
		if(arr->end == arr->capacity) {
				arr->capacity *= 2;
				arr->data = (uint8_t *) realloc(arr->data,
																				arr->capacity * sizeof(uint8_t));
		}
}

UInt8Array *
uint8_array_create(size_t initial_size)
{
		UInt8Array *arr = malloc(sizeof(UInt8Array));
		arr->data = (uint8_t *) calloc(initial_size, sizeof(uint8_t));
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
uint8_array_init(UInt8Array *arr, size_t size)
{
		arr->data = (uint8_t *) calloc(size, sizeof(uint8_t));
		arr->capacity = size;
		arr->end = 0;
}

void
uint8_array_clear(UInt8Array *arr)
{
		arr->end = 0;
}

uint8_t
uint8_array_push(UInt8Array *arr, uint8_t val)
{
		_check_array_size(arr);
		arr->data[arr->end++] = val;
		return val;
}

uint8_t
uint8_array_pop(UInt8Array *arr)
{
		if(arr->end > 0) {
				return arr->data[arr->end--];
		}
		return 0;
}

void
uint8_array_insert(UInt8Array *arr, const uint8_t *vals, size_t vals_size)
{
		if(vals_size == 0)
				return;

		/* Can we fit the new values without resizing? */
		if(vals_size + arr->end <= arr->capacity) {
				memcpy(arr->data + arr->end, vals, vals_size);
				arr->end += vals_size;
		} else {
				/* The size includes unend data in the original arr, so that
				   we can avoid resizing. */
				size_t new_size = arr->capacity + vals_size;
				uint8_t *new_array = (uint8_t *) malloc(new_size);
				memcpy(new_array, arr->data, arr->end); /* Copy current data */
				memcpy(new_array + arr->end, vals, vals_size); /* Copy new data */
				free(arr->data);
				arr->data = new_array;
				arr->capacity = new_size;
				arr->end += vals_size;
		}
		/* Ensure array is sized correctly anyway */
		_check_array_size(arr);
}
