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
        for mode in ['a+', 'w+', 'ab', 'r+', 'U', 'x', 'xb']:
            with self.assertRaisesRegexp(ValueError, '^Invalid mode: .*$'):
                EncodedFile(mode=mode)

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
        fp = heatshrink.open(self.TEST_FILENAME, 'wb')
        self.assertTrue(not fp.closed)
        fp.close()
        self.assertTrue(fp.closed)

    def test_context_manager(self):
        with heatshrink.open(self.TEST_FILENAME, 'wb') as fp:
            fp.write('Testing\n')
            fp.write('One, two...')

        self.assertTrue(fp.closed)

    def test_operations_on_closed_file(self):
        fp = heatshrink.open(self.TEST_FILENAME, 'wb')
        fp.close()
        self.assertRaises(ValueError, fp.write, 'abcde')
        self.assertRaises(ValueError, fp.seek, 0)

        fp = heatshrink.open(self.TEST_FILENAME, 'rb')
        fp.close()
        self.assertRaises(ValueError, fp.read)
        self.assertRaises(ValueError, fp.seek, 0)

    def test_cannot_write_in_read_mode(self):
        # Write some junk data
        with open(self.TEST_FILENAME, 'wb') as fp:
            fp.write(b'abcde')

        with heatshrink.open(self.TEST_FILENAME) as fp:
            self.assertTrue(fp.readable())
            self.assertTrue(not fp.writeable())
            self.assertRaises(IOError, fp.write, 'abcde')

    def test_cannot_read_in_write_mode(self):
        with heatshrink.open(self.TEST_FILENAME, 'wb') as fp:
            self.assertTrue(fp.writeable())
            self.assertTrue(not fp.readable())
            self.assertRaises(IOError, fp.read)

    @unittest.skip('Not implemented')
    def test_seeking_forwards(self):
        pass

    @unittest.skip('Not implemented')
    def test_seeking_backwards(self):
        with heatshrink.open(self.TEST_FILENAME, 'wb') as fp:
            fp.write('abcde')

        with heatshrink.open(self.TEST_FILENAME) as fp:
            contents = fp.read(100)
            # Reset and re-read
            fp.seek(0)
            self.assertEqual(fp.read(100), contents)

    def test_tell(self):
        with heatshrink.open(self.TEST_FILENAME, 'wb') as fp:
            bytes_written = fp.write('abcde')
            self.assertEqual(fp.tell(), bytes_written)

        with heatshrink.open(self.TEST_FILENAME) as fp:
            fp.read(3)
            self.assertEqual(fp.tell(), 3)

    @unittest.skip('Not implemented')
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

    @unittest.skip('Not implemented')
    def test_readline(self):
        lines = ['Line one', 'Line two', 'All the lines']

        with heatshrink.open(self.TEST_FILENAME, 'wb') as fp:
            fp.write('\n'.join(lines))

        with heatshrink.open(self.TEST_FILENAME, 'rb') as fp:
            for line in lines:
                self.assertEqual(fp.readline(), line)

    @unittest.skip('Not implemented')
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
