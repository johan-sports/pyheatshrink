#include <stdarg.h>
#include <stddef.h>
#include <setjmp.h>
#include <cmocka.h>

#include <dynamic_arrays.h>

void test_uint8_array_create(void)
{
    UInt8Array *arr = uint8_array_create(10);
    assert_non_null(arr);
    assert_non_null(arr->data);
    assert_int_equal(arr->capacity, 10);
    assert_int_equal(arr->end, 0);

    uint8_array_free(arr);
}

void test_uint8_array_free()
{
    UInt8Array *arr = uint8_array_create(10);
    uint8_array_free(arr);
}


void test_uint8_array_clear(void)
{
    UInt8Array *arr = uint8_array_create(10);
		uint8_t new_items[] = {1, 2};
		uint8_array_insert(arr, new_items, 2);
    uint8_array_clear(arr);
    assert_int_equal(arr->capacity, 10);
    assert_int_equal(arr->end, 0);

    uint8_array_free(arr);
}

void test_uint8_array_insert(void)
{
    UInt8Array *arr = uint8_array_create(5);
    assert_int_equal(arr->capacity, 5);

    /* Enough capacity currently to fit new items */
    uint8_t new_items[] = {1, 2, 3, 4};
    uint8_array_insert(arr, new_items, 4);
    assert_int_equal(arr->capacity, 5);
    assert_int_equal(arr->end, 4);

    uint8_array_insert(arr, new_items, 4);
    assert_int_equal(arr->capacity, 9); /* Recapacity current capacity + new */
    assert_int_equal(arr->end, 8);

    /* Insert just enough to hit the capacity limit */
    uint8_array_insert(arr, new_items, 1);
    assert_int_equal(arr->capacity, 9);
    assert_int_equal(arr->end, 9);

    uint8_t expected_arr[] = {1, 2, 3, 4, 1, 2, 3, 4, 1};
    assert_memory_equal(arr->data, expected_arr, 9);

    uint8_array_free(arr);
}

void test_uint8_array_copy(void)
{
    UInt8Array *arr = uint8_array_create(5);
    uint8_t new_items[] = {1, 2, 3, 4, 5};
    uint8_array_insert(arr, new_items, 5);

    uint8_t *copied = uint8_array_copy(arr);
    assert_memory_equal(arr->data, copied, 5);
    /* Ensure copy */
    assert_ptr_not_equal(arr->data, copied);

    uint8_array_free(arr);

    /* Ensure copy remains after original array free */
    assert_memory_equal(copied, new_items, 5);
    free(copied);
}

void test_uint8_array_helpers(void)
{
    UInt8Array *arr = uint8_array_create(8);

    assert_int_equal(uint8_array_count(arr), 0);
    assert_int_equal(uint8_array_end(arr), 0);
    assert_int_equal(uint8_array_capacity(arr), 8);
		uint8_t new_items[] = {1, 2, 3, 4, 5};
		uint8_array_insert(arr, new_items, 5);

    assert_int_equal(uint8_array_first(arr), 1);
    assert_int_equal(uint8_array_last(arr), 5);

    uint8_array_free(arr);
}

int main(void)
{
    const struct CMUnitTest tests[] = {
        cmocka_unit_test(test_uint8_array_create),
        cmocka_unit_test(test_uint8_array_free),
        cmocka_unit_test(test_uint8_array_clear),
        cmocka_unit_test(test_uint8_array_insert),
        cmocka_unit_test(test_uint8_array_copy),
        cmocka_unit_test(test_uint8_array_helpers),
    };

    return cmocka_run_group_tests(tests, NULL, NULL);
}
