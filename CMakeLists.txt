cmake_minimum_required(VERSION 2.8)
project(pyheatshrink)

include(CTest)

add_subdirectory(src)
add_subdirectory(ctests)

enable_testing()
