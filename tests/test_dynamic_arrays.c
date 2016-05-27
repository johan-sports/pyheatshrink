#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>

#include <dynamic_arrays.h>

void test_uint8_array_alloc(void)
{
		UInt8Array *arr = uint8_array_alloc(10);
		assert_not_null(arr);
		assert_not_null(arr->items);
		assert_int_equal(arr->size, 10);
		assert_int_equal(arr->used, 0);

		uint8_array_free(arr);
}

void test_uint8_array_free()
{
		UInt8Array *arr = uint8_array_alloc(10);
		uint8_array_free(arr);
}


void test_uint8_array_clear(void)
{
		UInt8Array *arr = uint8_array_alloc(10);
		uint8_array_push(arr, 1);
		uint8_array_push(arr, 2);
		uint8_array_clear(arr);
		//assert_int_equal(arr->items, NULL);
		assert_int_equal(arr->size, 10);
		assert_int_equal(arr->used, 0);

		uint8_array_free(arr);
}

void test_uint8_array_push(void)
{
		UInt8Array *arr = uint8_array_alloc(3);
		uint8_array_push(arr, 1);
		uint8_array_push(arr, 2);

		uint8_t expected_arr[] = {1, 2, 0};
		// assert_int_equal(*arr->items, expected_arr); /* May need to use different assert */
		assert_int_equal(arr->size, 3);
		assert_int_equal(arr->used, 2);

		uint8_array_free(arr);
}

void test_uint8_array_push_resizing(void)
{
		UInt8Array *arr = uint8_array_alloc(2);

		uint8_array_push(arr, 1);
		assert_int_equal(arr->used, 1);
		assert_int_equal(arr->size, 2);

		uint8_array_push(arr, 2);
		assert_int_equal(arr->used, 2);
		assert_int_equal(arr->size, 2);

		/* Resized here */
		uint8_array_push(arr, 3);
		assert_int_equal(arr->used, 3);
		assert_int_equal(arr->size, 4);

		uint8_array_free(arr);
}

void test_uint8_array_insert(void)
{
		UInt8Array *arr = uint8_array_alloc(5);
		assert_int_equal(arr->size, 5);

		/* Enough size currently to fit new items */
		uint8_t new_items[] = {1, 2, 3, 4};
		uint8_array_insert(arr, new_items, 4);
		assert_int_equal(arr->size, 5);
		assert_int_equal(arr->used, 4);

		uint8_array_insert(arr, new_items, 4);
		assert_int_equal(arr->size, 9); /* Resize current size + new */
		assert_int_equal(arr->used, 8);

		/* Insert just enough to hit the size limit */
		uint8_array_insert(arr, new_items, 1);
		assert_int_equal(arr->size, 9);
		assert_int_equal(arr->used, 9);

		uint8_array_free(arr);
}


int main(void)
{
		const struct CMUnitTest tests[] = {
				cmocka_unit_test(test_uint8_array_alloc),
				cmocka_unit_test(test_uint8_array_free),
				cmocka_unit_test(test_uint8_array_clear),
				cmocka_unit_test(test_uint8_array_push),
				cmocka_unit_test(test_uint8_array_push_resizing),
				cmocka_unit_test(test_uint8_array_insert),
		};

		return cmocka_run_group_tests(tests, NULL, NULL);
}
