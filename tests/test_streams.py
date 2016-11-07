import io
import os
import unittest

from heatshrink.streams import EncodedFile

from .constants import LARGE_PARAGRAPH
from .utils import random_string


# TODO: Add test to see if compression parameters are
# TODO: passed to Reader/Writer
class EncodedFileTest(unittest.TestCase):
    TEST_FILENAME = 'test.bin'

    def tearDown(self):
        # Cleanup temporary file
        if os.path.exists(self.TEST_FILENAME):
            os.unlink(self.TEST_FILENAME)

    def test_bad_args(self):
        self.assertRaises(TypeError, EncodedFile, None)
        self.assertRaises(ValueError, EncodedFile, None, mode='eb')

    def test_invalid_modes(self):
        data = io.BytesIO()

        for mode in ['a+', 'w+', 'ab', 'r+', 'U', 'x', 'xb']:
            with self.assertRaisesRegexp(ValueError, '^Invalid mode: .*$'):
                EncodedFile(data, mode=mode)

    def test_round_trip(self):
        write_str = 'Testing\nAnd Stuff'

        # TODO: Consider using EncodedFile with StringIO
        with EncodedFile(self.TEST_FILENAME, mode='wb') as fp:
            fp.write(write_str)

        with EncodedFile(self.TEST_FILENAME) as fp:
            read_str = fp.read()

        self.assertEqual(write_str, read_str)

    def test_with_large_files(self):
        test_sizes = [1000, 10000, 100000]

        for size in test_sizes:
            contents = random_string(size)

            with EncodedFile(self.TEST_FILENAME, mode='wb') as fp:
                fp.write(contents)

            with EncodedFile(self.TEST_FILENAME) as fp:
                read_str = fp.read()

            if read_str != contents:
                msg = ('Decoded and original file contents '
                       'do not match for size: {}')
                self.fail(msg.format(size))

    def test_with_file_object(self):
        data = io.BytesIO()

        fp = EncodedFile(data, mode='wb')
        fp.write(LARGE_PARAGRAPH)
        data.seek(0)
        self.assertTrue(len(data.read()) > 0)
        fp.close()

    def test_closed_true_when_file_closed(self):
        fp = EncodedFile(self.TEST_FILENAME, mode='wb')
        self.assertTrue(not fp.closed)
        fp.close()
        self.assertTrue(fp.closed)

    def test_context_manager(self):
        with EncodedFile(self.TEST_FILENAME, mode='wb') as fp:
            fp.write('Testing\n')
            fp.write('One, two...')

        self.assertTrue(fp.closed)

    def test_operations_on_closed_file(self):
        fp = EncodedFile(self.TEST_FILENAME, mode='wb')
        fp.close()
        self.assertRaises(ValueError, fp.write, 'abcde')
        self.assertRaises(ValueError, fp.seek, 0)

        fp = EncodedFile(self.TEST_FILENAME, 'rb')
        fp.close()
        self.assertRaises(ValueError, fp.read)
        self.assertRaises(ValueError, fp.seek, 0)

    def test_cannot_write_in_read_mode(self):
        # Write some junk data
        with open(self.TEST_FILENAME, 'wb') as fp:
            fp.write(b'abcde')

        with EncodedFile(self.TEST_FILENAME) as fp:
            self.assertTrue(fp.readable())
            self.assertTrue(not fp.writable())
            self.assertRaises(IOError, fp.write, 'abcde')

    def test_cannot_read_in_write_mode(self):
        with EncodedFile(self.TEST_FILENAME, mode='wb') as fp:
            self.assertTrue(fp.writable())
            self.assertTrue(not fp.readable())
            self.assertRaises(IOError, fp.read)

    @unittest.skip('Not implemented')
    def test_seeking_forwards(self):
        pass

    @unittest.skip('Not implemented')
    def test_seeking_backwards(self):
        with EncodedFile(self.TEST_FILENAME, mode='wb') as fp:
            fp.write('abcde')

        with EncodedFile(self.TEST_FILENAME) as fp:
            contents = fp.read(100)
            # Reset and re-read
            fp.seek(0)
            self.assertEqual(fp.read(100), contents)

    def test_tell(self):
        with EncodedFile(self.TEST_FILENAME, mode='wb') as fp:
            bytes_written = fp.write('abcde')
            self.assertEqual(fp.tell(), bytes_written)

        with EncodedFile(self.TEST_FILENAME) as fp:
            fp.read(3)
            self.assertEqual(fp.tell(), 3)

    @unittest.skip('Not implemented')
    def test_peek(self):
        pass

    #################
    # Reading
    #################
    def test_read_whole_file(self):
        with EncodedFile(self.TEST_FILENAME, mode='wb') as fp:
            fp.write(LARGE_PARAGRAPH)

        with EncodedFile(self.TEST_FILENAME) as fp:
            read_str = fp.read()

        self.assertEqual(LARGE_PARAGRAPH, read_str)

    def test_read_buffered(self):
        with EncodedFile(self.TEST_FILENAME, mode='wb') as fp:
            fp.write(LARGE_PARAGRAPH)

        READ_SIZE = 128
        offset = 0

        with EncodedFile(self.TEST_FILENAME) as fp:
            while True:
                contents = fp.read(READ_SIZE)

                if not contents:
                    break

                self.assertEqual(
                    contents,
                    LARGE_PARAGRAPH[offset:offset+READ_SIZE]
                )
                offset += READ_SIZE

    def test_readinto(self):
        pass

    #################
    # Writing
    #################
    def test_write(self):
        with EncodedFile(self.TEST_FILENAME, mode='wb') as fp:
            BUFFER_SIZE = 16
            # StringIO makes it easy to buffer
            text_buf = io.BytesIO(LARGE_PARAGRAPH.encode('utf8'))

            while True:
                chunk = text_buf.read(BUFFER_SIZE)

                if not chunk:
                    break

                fp.write(chunk)

        with EncodedFile(self.TEST_FILENAME) as fp:
            self.assertEqual(fp.read(), LARGE_PARAGRAPH)

    def test_remaining_data_flushed_on_close(self):
        fp = EncodedFile(self.TEST_FILENAME, mode='wb')
        fp.write(LARGE_PARAGRAPH)
        fp.close()
