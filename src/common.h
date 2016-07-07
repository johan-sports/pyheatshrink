#ifndef _PY_HS_UTILS__
#define _PY_HS_UTILS__

#include <stdio.h>

#ifdef NDEBUG
#define log_debug(msg, ...) ((void) 0) /* Do nothing */
#else
#define log_debug(msg, ...)                                             \
    fprintf(stdout, "[DEBUG] (%s:%d) " msg "\n", __FILE__, __LINE__, ##__VA_ARGS__)
#endif /* NDEBUG */

#ifdef UNIT_TESTING
/* Redefine allocation functions */
extern void *
_test_malloc(const size_t, const char *file, const int line);
extern void *
_test_calloc(const size_t number_of_elements, const size_t size,
						 const char *file, const int line);
extern void *
_test_realloc(void *const ptr, size_t size,
							const char *file, const int line);
extern void
_test_free(void *const ptr, const char *file, const int line);

#define malloc(size) _test_malloc(size, __FILE__, __LINE__)
#define calloc(num, size) _test_calloc(num, size, __FILE__, __LINE__)
#define realloc(ptr, size) _test_realloc(ptr, size, __FILE__, __LINE__)
#define free(ptr) _test_free(ptr, __FILE__, __LINE__)

/* Redefine assert */
extern void
mock_assert(const int result, const char *const expression,
						const char *const file, const int line);
#define PyHS_assert(expr) \
		mock_assert((int) (expr), #expr, __FILE__, __LINE__);
#else
#include <stdlib.h>

#include <assert.h>
#define PyHS_assert assert
#endif /* UNIT_TESTING */

#endif /* _PY_HS_UTILS__ */
