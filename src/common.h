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
