import array
import functools
import io
import os
import unittest

from heatshrink.streams import EncodedFile

from .constants import LARGE_PARAGRAPH
from .utils import random_string

TEST_FILENAME = 'test_{}_tmp'.format(os.getpid())


# TODO: Add test to see if compression parameters are
# TODO: passed to Reader/Writer
class EncodedFileTest(unittest.TestCase):
    def setUp(self):
        self.fp = EncodedFile(TEST_FILENAME, 'wb')

    def tearDown(self):
        if self.fp:
            self.fp.close()

        # Cleanup temporary file
        if os.path.exists(TEST_FILENAME):
            os.unlink(TEST_FILENAME)

    def test_bad_args(self):
        self.assertRaises(TypeError, EncodedFile, None)
        self.assertRaises(ValueError, EncodedFile, None, mode='eb')

    def test_invalid_modes(self):
        data = io.BytesIO()

        for mode in ['a+', 'w+', 'ab', 'r+', 'U', 'x', 'xb']:
            with self.assertRaisesRegexp(ValueError, '^Invalid mode: .*$'):
                EncodedFile(data, mode=mode)

    def test_round_trip(self):
        write_str = b'Testing\nAnd Stuff'

        # TODO: Consider using EncodedFile with StringIO
        self.fp.write(write_str)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        self.assertEqual(self.fp.read(), write_str)

    def test_with_large_files(self):
        test_sizes = [1000, 10000, 100000]

        for size in test_sizes:
            contents = random_string(size)

            with EncodedFile(TEST_FILENAME, mode='wb') as fp:
                fp.write(contents)

            with EncodedFile(TEST_FILENAME) as fp:
                read_str = fp.read()

            if read_str != contents:
                msg = ('Decoded and original file contents '
                       'do not match for size: {}')
                self.fail(msg.format(size))

    def test_with_file_object(self):
        plain_file = open(TEST_FILENAME, 'wb')
        encoded_file = EncodedFile(plain_file, mode='wb')

        encoded_file.write(LARGE_PARAGRAPH)
        # Flush data
        encoded_file.close()
        self.assertTrue(encoded_file.closed)
        # Should close the plain file too, as it "owns" it.
        self.assertTrue(plain_file.closed)

        with open(TEST_FILENAME, 'rb') as fp:
            self.assertTrue(len(fp.read()) > 0)

    def test_closed_true_when_file_closed(self):
        self.assertFalse(self.fp.closed)
        self.fp.close()
        self.assertTrue(self.fp.closed)

    def test_context_manager(self):
        with EncodedFile(TEST_FILENAME, mode='wb') as fp:
            fp.write(b'Testing\n')
            fp.write(b'One, two...')

        self.assertTrue(fp.closed)

    def test_operations_on_closed_file(self):
        self.fp.close()
        self.assertRaises(ValueError, self.fp.write, b'abcde')
        self.assertRaises(ValueError, self.fp.seek, 0)

        self.fp = EncodedFile(TEST_FILENAME, 'rb')
        self.fp.close()
        self.assertRaises(ValueError, self.fp.read)
        self.assertRaises(ValueError, self.fp.seek, 0)

    def test_cannot_write_in_read_mode(self):
        # Write some junk data
        self.fp.write(b'abcde')
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        self.assertTrue(self.fp.readable())
        self.assertFalse(self.fp.writable())
        self.assertRaises(IOError, self.fp.write, b'abcde')

    def test_cannot_read_in_write_mode(self):
        self.assertTrue(self.fp.writable())
        self.assertFalse(self.fp.readable())
        self.assertRaises(IOError, self.fp.read)

    def test_seeking_forwards(self):
        contents = random_string(250)
        self.fp.write(contents)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        self.assertEqual(self.fp.read(100), contents[:100])
        self.fp.seek(50, io.SEEK_CUR)  # Move 50 forwards
        self.assertEqual(self.fp.read(100), contents[-100:])

    def test_seeking_backwards(self):
        self.fp.write(b'abcde')
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        contents = self.fp.read(100)
        # Reset and re-read
        self.fp.seek(0)
        self.assertEqual(self.fp.read(100), contents)

    def test_seeking_from_end(self):
        self.fp.write(LARGE_PARAGRAPH)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        self.assertEqual(self.fp.read(100), LARGE_PARAGRAPH[:100])
        self.fp.seek(-100, io.SEEK_END)
        self.assertEqual(self.fp.read(100), LARGE_PARAGRAPH[-100:])

    def test_tell(self):
        bytes_written = self.fp.write(b'abcde')
        self.assertEqual(self.fp.tell(), bytes_written)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        self.fp.read(3)
        self.assertEqual(self.fp.tell(), 3)

    def test_peek(self):
        self.fp.write(LARGE_PARAGRAPH)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        pdata = self.fp.peek()
        self.assertNotEqual(len(pdata), 0)
        self.assertTrue(LARGE_PARAGRAPH.startswith(pdata))
        self.assertEqual(self.fp.read(), LARGE_PARAGRAPH)

    #################
    # Reading
    #################
    def test_read_whole_file(self):
        self.fp.write(LARGE_PARAGRAPH)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        read_str = self.fp.read()
        self.assertEqual(LARGE_PARAGRAPH, read_str)

    def test_read_buffered(self):
        self.fp.write(LARGE_PARAGRAPH)
        self.fp.close()

        READ_SIZE = 128
        offset = 0

        self.fp = EncodedFile(TEST_FILENAME)
        read_buf = functools.partial(self.fp.read, READ_SIZE)

        for i, contents in enumerate(iter(read_buf, '')):
            offset = READ_SIZE * i
            self.assertEqual(
                contents,
                LARGE_PARAGRAPH[offset: offset + READ_SIZE]
            )

    def test_read_one_char(self):
        self.fp.write(LARGE_PARAGRAPH)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        for c in LARGE_PARAGRAPH:
            self.assertEqual(self.fp.read(1), c)

    def test_read1(self):
        raise AssertionError('TODO')

    def test_readinto(self):
        self.fp.write(b'abcde')
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        a = array.array('b', b'x' * 10)  # Fill with junk
        n = self.fp.readinto(a)
        try:
            # Python 3
            self.assertEqual(b'abcde', a.tobytes()[:n])
        except AttributeError:
            self.assertEqual(b'abcde', a.tostring()[:n])

    def test_readline(self):
        self.fp.write(LARGE_PARAGRAPH)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        lines = LARGE_PARAGRAPH.splitlines()

        for index, line in enumerate(iter(self.fp.readline, '')):
            self.assertEqual(line, lines[index] + '\n')

    def test_readline_iterator(self):
        self.fp.write(LARGE_PARAGRAPH)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        lines = LARGE_PARAGRAPH.splitlines()

        for i, line in enumerate(self.fp):
            self.assertEqual(line, lines[i] + '\n')

    def test_readlines(self):
        self.fp.write(LARGE_PARAGRAPH)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        lines = self.fp.readlines()
        self.assertEqual(''.join(lines), LARGE_PARAGRAPH)

    #################
    # Writing
    #################
    def test_write(self):
        BUFFER_SIZE = 16
        # StringIO makes it easy to buffer
        text_buf = io.BytesIO(LARGE_PARAGRAPH.encode('utf8'))

        while True:
            chunk = text_buf.read(BUFFER_SIZE)

            if not chunk:
                break

            self.fp.write(chunk)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        self.assertEqual(self.fp.read(), LARGE_PARAGRAPH)

    def test_remaining_data_flushed_on_close(self):
        self.fp.write(LARGE_PARAGRAPH)

        with open(TEST_FILENAME) as read_fp:
            self.assertEqual(len(read_fp.read()), 0)

        self.fp.close()

        with open(TEST_FILENAME) as read_fp:
            self.assertTrue(len(read_fp.read()) > 0)

    def test_writelines(self):
        raise AssertionError('TODO')
