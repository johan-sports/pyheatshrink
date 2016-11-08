import os
import time

import heatshrink

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

PLAIN_FILE_PATH = os.path.join(DATA_DIR, 'plain_file.txt')
COMPRESSED_FILE_PATH = os.path.join(DATA_DIR, 'compressed_file.txt')


def timed(f):
    """Wraps function f and prints timing information.

    Timing is from when the function from function beginning
    to end in seconds.
    """
    def wrap(*args):
        initial = time.time()
        ret = f(*args)
        elapsed = time.time() - initial
        print('==> {}s elapsed'.format(elapsed))
        return ret
    return wrap


def run_benchmark(filename, f):
    """Load a file and benchmark against function f."""
    with open(filename, 'rb') as fp:
        contents = fp.read()

    timed_f = timed(f)

    print('*** Reading 10,000 bytes ***')
    timed_f(contents[:10000])

    print('*** Reading 1,000,000 bytes ***')
    timed_f(contents[:1000000])

    print('*** Reading whole file ({} bytes) ***'.format(len(contents)))
    result = timed_f(contents)

    return result


def print_block(msg, size=50):
    sep = '=' * size
    print(sep)
    print(msg)
    print(sep)


def main():
    print_block('Encode benchmarks')
    encoded = run_benchmark(PLAIN_FILE_PATH, heatshrink.encode)
    # Store encoded data for use py the decoder
    with open(COMPRESSED_FILE_PATH, 'wb') as fp:
        fp.write(encoded)

    print_block('Decode benchmarks')
    run_benchmark(COMPRESSED_FILE_PATH, heatshrink.decode)


if __name__ == '__main__':
    main()
