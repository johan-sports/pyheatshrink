#include "dynamic_arrays.h"

#include <string.h>

#define CHECK_ARRAY_SIZE(arr, type)																			\
		if(arr->used == arr->size) {																				\
				arr->size *= 2;																									\
				arr->items = (type *) realloc(arr->items, arr->size * sizeof(type)); \
		}

UInt8Array *
uint8_array_alloc(size_t initial_size)
{
		UInt8Array *arr = NEW(UInt8Array);
		arr->items = (uint8_t *) calloc(initial_size, sizeof(uint8_t));
		arr->size = 0;
		arr->used = 0;
		return arr;
}

void
uint8_array_free(UInt8Array *arr)
{
		if(arr != NULL) {
				if(arr->items != NULL) {
						free(arr->items);
						arr->items = NULL;
				}
				free(arr);
		}
}

void
uint8_array_init(UInt8Array *arr, size_t size)
{
		arr->items = (uint8_t *) calloc(size, sizeof(uint8_t));
		arr->size = size;
		arr->used = 0;
}

void
uint8_array_clear(UInt8Array *arr)
{
		arr->used = 0;
}

uint8_t
uint8_array_push(UInt8Array *arr, uint8_t val)
{
		CHECK_ARRAY_SIZE(arr, uint8_t);
		arr->items[arr->used++] = val;
		return val;
}

void
uint8_array_insert(UInt8Array *arr, const uint8_t *vals, size_t vals_size)
{
		/* Can we fit the new values without resizing? */
		if(vals_size + arr->used <= arr->size) {
				memcpy(arr->items + arr->used, vals, vals_size);
				arr->used += vals_size;
				CHECK_ARRAY_SIZE(arr, uint8_t);
		} else {
				size_t new_size = arr->size + vals_size;
				uint8_t *new_array = (uint8_t *) malloc(new_size);
				memcpy(new_array, arr->items, arr->used);
				memcpy(new_array + arr->used, vals, vals_size);
				free(arr->items);
				arr->items = new_array;
				arr->size = new_size;
				arr->used += vals_size;
		}
}

void
uint8_array_insert_dyn(UInt8Array *arr, const uint8_t *vals)
{
		return uint8_array_insert(arr, vals, ARRAY_SIZE(vals));
}
