find_package(CMocka REQUIRED)

# Add definitions specific to the testing environment
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -DUNIT_TESTING -g -O0")

include_directories("${CMOCKA_INCLUDE_DIR}")
include_directories("${PROJECT_SOURCE_DIR}")
include_directories("${PROJECT_SOURCE_DIR}/src")

# test_dynamic_arrays.c
add_executable(test_dynamic_arrays test_dynamic_arrays.c)
add_test(test_dynamic_arrays test_dynamic_arrays)

target_link_libraries(test_dynamic_arrays pyheatshrink ${CMOCKA_LIBRARIES})
