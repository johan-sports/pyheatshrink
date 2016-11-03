import os
import unittest

import heatshrink

from .constants import LARGE_PARAGRAPH
from .utils import random_string


class EncodedFileTest(unittest.TestCase):
    def test_round_robin(self):
        filename = 'test.bin'
        write_str = 'Testing\nAnd Stuff'

        # TODO: Consider using EncodedFile with StringIO
        with heatshrink.open(filename, 'wb') as fp:
            fp.write(write_str)

        with heatshrink.open(filename, 'rb') as fp:
            read_str = fp.read()

        os.unlink(filename)
        self.assertEqual(write_str, read_str)

    def test_large_file(self):
        filename = 'test.bin'

        with heatshrink.open(filename, 'wb') as fp:
            fp.write(LARGE_PARAGRAPH)

        with heatshrink.open(filename, 'rb') as fp:
            read_str = fp.read()

        os.unlink(filename)
        self.assertEqual(LARGE_PARAGRAPH, read_str)

    def test_with_large_files(self):
        filename = 'test.bin'
        test_sizes = [1000, 10000, 100000]

        for size in test_sizes:
            contents = random_string(size)

            with heatshrink.open(filename, 'wb') as fp:
                fp.write(contents)

            with heatshrink.open(filename, 'rb') as fp:
                read_str = fp.read()

            os.unlink(filename)
            if read_str != contents:
                msg = ('Decoded and original file contents '
                       'do not match for size: {}')
                self.fail(msg.format(size))

    def test_read_lines(self):
        filename = 'test.bin'
        lines = ['Line one', 'Line two', 'All the lines']

        with heatshrink.open(filename, 'wb') as fp:
            fp.write('\n'.join(lines))

        with heatshrink.open(filename, 'rb') as fp:
            # String contents already contains the newlines
            read_str = ''.join([line for line in fp])

        os.unlink(filename)
        self.assertEqual('\n'.join(lines), read_str)
