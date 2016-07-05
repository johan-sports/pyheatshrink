import time
import heatshrink
import urllib2


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
    encoded = run_benchmark('plain_file.txt', heatshrink.encode)
    # Store encoded data for use py the decoder
    with open('compressed_file.txt', 'wb') as fp:
        fp.write(encoded)

    print_block('Decode benchmarks')
    run_benchmark('compressed_file.txt', heatshrink.decode)


if __name__ == '__main__':
    main()
