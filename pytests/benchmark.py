import os
import time

import heatshrink

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

PLAIN_FILE_PATH = os.path.join(DATA_DIR, 'plain_file.txt')
COMPRESSED_FILE_PATH = os.path.join(DATA_DIR, 'compressed_file.txt')


def run_benchmark(filename, fn):
    with open(filename, 'rb') as fp:
        contents = fp.read()

    print('*** Reading 10,000 bytes ***')
    t0 = time.time()
    fn(contents[:10000])
    elapsed = time.time() - t0
    print('==> {}s elapsed'.format(elapsed))

    print('*** Reading 1,000,000 bytes ***')
    t0 = time.time()
    fn(contents[:1000000])
    elapsed = time.time() - t0
    print('==> {}s elapsed'.format(elapsed))

    print('*** Reading whole file ({} bytes) ***'.format(len(contents)))
    t0 = time.time()
    result = fn(contents)
    elapsed = time.time() - t0
    print('==> {}s elapsed'.format(elapsed))

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
