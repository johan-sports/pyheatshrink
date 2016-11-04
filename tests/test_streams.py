import os
import unittest

import heatshrink
from heatshrink.streams import EncodedFile

from .constants import LARGE_PARAGRAPH
from .utils import random_string


class EncodedFileTest(unittest.TestCase):
    TEST_FILENAME = 'test.bin'

    def tearDown(self):
        # Cleanup temporary file
        if os.path.exists(self.TEST_FILENAME):
            os.unlink(self.TEST_FILENAME)

    def test_bad_args(self):
        self.assertRaises(ValueError, EncodedFile, file=None, filename=None)
        self.assertRaises(ValueError, EncodedFile, mode='eb')

    def test_invalid_modes(self):
        pass

    def test_round_robin(self):
        write_str = 'Testing\nAnd Stuff'

        # TODO: Consider using EncodedFile with StringIO
        with heatshrink.open(self.TEST_FILENAME, 'wb') as fp:
            fp.write(write_str)

        with heatshrink.open(self.TEST_FILENAME, 'rb') as fp:
            read_str = fp.read()

        self.assertEqual(write_str, read_str)

    def test_large_file(self):
        with heatshrink.open(self.TEST_FILENAME, 'wb') as fp:
            fp.write(LARGE_PARAGRAPH)

        with heatshrink.open(self.TEST_FILENAME, 'rb') as fp:
            read_str = fp.read()

        self.assertEqual(LARGE_PARAGRAPH, read_str)

    def test_with_large_files(self):
        test_sizes = [1000, 10000, 100000]

        for size in test_sizes:
            contents = random_string(size)

            with heatshrink.open(self.TEST_FILENAME, 'wb') as fp:
                fp.write(contents)

            with heatshrink.open(self.TEST_FILENAME, 'rb') as fp:
                read_str = fp.read()

            if read_str != contents:
                msg = ('Decoded and original file contents '
                       'do not match for size: {}')
                self.fail(msg.format(size))

    def test_closed_true_when_file_closed(self):
        pass

    def test_context_manager(self):
        pass

    def test_cannot_write_in_read_mode(self):
        pass

    def test_cannot_read_in_write_mode(self):
        pass

    def test_seeking_forwards(self):
        pass

    def test_seeking_backwards(self):
        pass

    def test_tell(self):
        pass

    def test_peek(self):
        pass

    #################
    # Reading
    #################
    def test_read_whole_file(self):
        pass

    def test_read_buffered(self):
        pass

    def test_read_eof(self):
        pass

    def test_readinto(self):
        pass

    def test_readline(self):
        lines = ['Line one', 'Line two', 'All the lines']

        with heatshrink.open(self.TEST_FILENAME, 'wb') as fp:
            fp.write('\n'.join(lines))

        with heatshrink.open(self.TEST_FILENAME, 'rb') as fp:
            for line in lines:
                self.assertEqual(fp.readline(), line)

    def test_readlines(self):
        pass

    #################
    # Writing
    #################
    def test_write(self):
        pass

    def test_remaining_data_flushed_on_close(self):
        pass

    def test_writelines(self):
        pass
