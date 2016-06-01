#ifndef _PY_HS_UTILS__
#define _PY_HS_UTILS__

#ifdef TESTING
extern void mock_assert(const int result, const char *const expression,
												const char *const file, const int line);
#define PyHS_assert(expr) \
		mock_assert((int) (expr), #expr, __FILE__, __LINE__);
#else
#include <assert.h>

#define PyHS_assert assert
#endif /* UNIT_TESTING */

#endif /* _PY_HS_UTILS__ */
