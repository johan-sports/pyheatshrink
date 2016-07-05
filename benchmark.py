import time
import heatshrink


def encode_bench(filename):
    with open(filename, 'rb') as fp:
        contents = fp.read()

    print('*** Reading 10,000 bytes ***')
    t0 = time.time()
    heatshrink.encode(contents[:10000])
    elapsed = time.time() - t0
    print('==> {}s elapsed'.format(elapsed))

    print('*** Reading 1,000,000 bytes ***')
    t0 = time.time()
    heatshrink.encode(contents[:1000000])
    elapsed = time.time() - t0
    print('==> {}s elapsed'.format(elapsed))

    print('*** Reading whole file ({} bytes) ***'.format(len(contents)))
    t0 = time.time()
    heatshrink.encode(contents)
    elapsed = time.time() - t0
    print('==> {}s elapsed'.format(elapsed))


def decode_bench(filename):
    with open(filename, 'rb') as fp:
        contents = fp.read()

    print('*** Reading 10,000 bytes ***')
    t0 = time.time()
    heatshrink.decode(contents[:10000])
    elapsed = time.time() - t0
    print('==> {}s elapsed'.format(elapsed))

    print('*** Reading 1,000,000 bytes ***')
    t0 = time.time()
    heatshrink.decode(contents[:1000000])
    elapsed = time.time() - t0
    print('==> {}s elapsed'.format(elapsed))

    print('*** Reading whole file ({} bytes) ***'.format(len(contents)))
    t0 = time.time()
    heatshrink.decode(contents)
    elapsed = time.time() - t0
    print('==> {}s elapsed'.format(elapsed))


def print_block(msg, size=50):
    sep = '=' * size
    print(sep)
    print(msg)
    print(sep)


def main():
    print_block('Encode benchmarks')
    encode_bench('plain_file.txt')
    print_block('Decode benchmarks')
    decode_bench('compressed_file.txt')


if __name__ == '__main__':
    main()
