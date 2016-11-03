import random
import string


def random_string(size):
    """
    Generate a random string of size `size`.
    """
    choices = string.lowercase + string.uppercase + string.digits + '\n'
    return ''.join(random.choice(choices) for _ in range(size))
