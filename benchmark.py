import time
import heatshrink


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
    fn(contents)
    elapsed = time.time() - t0
    print('==> {}s elapsed'.format(elapsed))


def print_block(msg, size=50):
    sep = '=' * size
    print(sep)
    print(msg)
    print(sep)


def main():
    print_block('Encode benchmarks')
    run_benchmark('plain_file.txt', heatshrink.encode)
    print_block('Decode benchmarks')
    run_benchmark('compressed_file.txt', heatshrink.decode)


if __name__ == '__main__':
    main()
