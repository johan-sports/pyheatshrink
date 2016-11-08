import array
import functools
import io
import os
import unittest

from heatshrink.streams import EncodedFile

from .constants import TEXT, COMPRESSED
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
        EncodedFile(TEST_FILENAME, mode='wb', invalid_param=True).close()

    def test_different_compress_params(self):
        contents = b'abcde'
        with EncodedFile(TEST_FILENAME, 'wb',
                         window_sz2=8,
                         lookahead_sz2=5) as fp:
            fp.write(contents)

        with EncodedFile(TEST_FILENAME) as fp:
            # Decompressed data should just be junk
            self.assertNotEqual(fp.read(), contents)

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

        encoded_file.write(TEXT)
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
        contents = TEXT

        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            self.assertEqual(fp.read(100), contents[:100])
            fp.seek(50, io.SEEK_CUR)  # Move 50 forwards
            self.assertEqual(fp.read(100), contents[150:250])

    def test_seeking_backwards(self):
        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            contents = fp.read(100)
            fp.seek(0)
            self.assertEqual(fp.read(100), contents)

    def test_seeking_from_end(self):
        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            self.assertEqual(fp.read(100), TEXT[:100])
            fp.seek(-100, io.SEEK_END)
            self.assertEqual(fp.read(100), TEXT[-100:])

    def test_tell(self):
        bytes_written = self.fp.write(b'abcde')
        self.assertEqual(self.fp.tell(), bytes_written)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        self.fp.read(3)
        self.assertEqual(self.fp.tell(), 3)

    def test_peek(self):
        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            pdata = fp.peek()
            self.assertNotEqual(len(pdata), 0)
            self.assertTrue(TEXT.startswith(pdata))
            self.assertEqual(fp.read(), TEXT)

    #################
    # Reading
    #################
    def test_read_whole_file(self):
        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            self.assertEqual(fp.read(), TEXT)

    def test_read_buffered(self):
        READ_SIZE = 128
        offset = 0

        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            read_buf = functools.partial(fp.read, READ_SIZE)

            for i, contents in enumerate(iter(read_buf, '')):
                offset = READ_SIZE * i
                self.assertEqual(
                    contents,
                    TEXT[offset: offset + READ_SIZE]
                )

    def test_read_one_char(self):
        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            for c in TEXT:
                self.assertEqual(fp.read(1), c)

    def test_read1(self):
        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            blocks = []
            while True:
                result = fp.read1()
                if not result:
                    break
            blocks.append(result)
            self.assertEqual(b''.join(blocks), TEXT)
            self.assertEqual(fp.read1(), b'')

    def test_read1_0(self):
        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            self.assertEqual(fp.read1(0), b'')

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
        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            lines = TEXT.splitlines()

            # Could also use zip
            for i, line in enumerate(iter(fp.readline, '')):
                self.assertEqual(line, lines[i] + '\n')

    def test_readline_iterator(self):
        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            lines = TEXT.splitlines()

            for file_line, original_line in zip(fp, lines):
                self.assertEqual(file_line, original_line + '\n')

    def test_readlines(self):
        with EncodedFile(io.BytesIO(COMPRESSED)) as fp:
            lines = fp.readlines()
            self.assertEqual(''.join(lines), TEXT)

    #################
    # Writing
    #################
    def test_write(self):
        BUFFER_SIZE = 16
        # BytesIO makes it easy to buffer
        text_buf = io.BytesIO(TEXT.encode('utf8'))

        while True:
            chunk = text_buf.read(BUFFER_SIZE)

            if not chunk:
                break

            self.fp.write(chunk)
        self.fp.close()

        self.fp = EncodedFile(TEST_FILENAME)
        self.assertEqual(self.fp.read(), TEXT)

    def test_remaining_data_flushed_on_close(self):
        self.fp.write(TEXT)

        with open(self.fp.name) as fp:
            self.assertEqual(len(fp.read()), 0)

        self.fp.close()

        with open(self.fp.name) as fp:
            self.assertTrue(len(fp.read()) > 0)

    def test_writelines(self):
        with io.BytesIO(TEXT) as fp:
            lines = fp.readlines()

        self.fp.writelines(lines)
        self.fp.close()

        with open(self.fp.name) as fp:
            self.assertEqual(fp.read(), COMPRESSED)
