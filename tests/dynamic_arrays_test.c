#include "../src/dynamic_arrays.h"

void test_uint8_array_alloc(void)
{
		UInt8Array *arr = uint8_array_alloc();
		TEST_ASSERT_EQUAL(arr->items, NULL);
		TEST_ASSERT_EQUAL(arr->size, 0);
		TEST_ASSERT_EQUAL(arr->used, 0);

		uint8_array_free(arr);
}

void test_uint8_array_free()
{
		/* UInt8Array *arr = uint8_array_alloc(); */
}

void test_uint8_array_init(void)
{
		UInt8Array *arr = uint8_array_alloc();
		uint8_array_init(arr, 10);
		TEST_ASSERT_NOT_EQUAL(arr->items, NULL);
		TEST_ASSERT_EQUAL(arr->size, 10);
		TEST_ASSERT_EQUAL(arr->used, 0);

		uint8_array_free(arr);
}

void test_uint8_array_clear(void)
{
		UInt8Array *arr = uint8_array_alloc();
		uint8_array_init(arr, 10);
		uint8_array_clear(arr);
		TEST_ASSERT_EQUAL(arr->items, NULL);
		TEST_ASSERT_EQUAL(arr->size, 0);
		TEST_ASSERT_EQUAL(arr->used, 0);

		uint8_array_free(arr);
}

void test_uint8_array_push(void)
{
		UInt8Array *arr = uint8_array_alloc();
		uint8_array_init(arr, 3);
		uint8_array_push(arr, 1);
		uint8_array_push(arr, 2);

		uint8_t expected_arr[] = {1, 2, 0};
		TEST_ASSERT_EQUAL(*arr->items, expected_arr); /* May need to use different assert */
		TEST_ASSERT_EQUAL(arr->size, 3);
		TEST_ASSERT_EQUAL(arr->used, 2);

		uint8_array_free(arr);
}

void test_uint8_array_resizing(void)
{
		UInt8Array *arr = uint8_array_alloc();
		uint8_array_init(arr, 2);

		uint8_array_push(arr, 1);
		TEST_ASSERT_EQUAL(arr->used, 1);
		TEST_ASSERT_EQUAL(arr->size, 2);

		uint8_array_push(arr, 2);
		TEST_ASSERT_EQUAL(arr->used, 2);
		TEST_ASSERT_EQUAL(arr->size, 4);

		uint8_array_push(arr, 3);
		TEST_ASSERT_EQUAL(arr->used, 3);
		TEST_ASSERT_EQUAL(arr->size, 4);

		uint8_array_free(arr);
}

void test_uint8_array_insert(void)
{
		
}

int main(void)
{
		UNITY_BEGIN();
		RUN_TEST(test_uint8_array_alloc);
		RUN_TEST();
		return UNITY_END();
}
