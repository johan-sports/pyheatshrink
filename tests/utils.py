import random
import string


class TestUtilsMixin(object):
    """Mixin that provides extra testing utilities."""

    def assertNotRaises(self, func, *args, **kwargs):
        """Ensure that the an exception isn't raised.

        An AssertionError is raised if calling func with
        the given argument triggers any exception.
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            msg = 'Expected no exception, but got {.__name__}'
            raise AssertionError(msg.format(e.__class__))


def random_string(size):
    """
    Generate a random string of size `size`.
    """
    choices = string.ascii_lowercase + string.ascii_uppercase + string.digits + '\n'
    return ''.join(random.choice(choices) for _ in range(size))
