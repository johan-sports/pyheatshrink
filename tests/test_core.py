import array
import unittest

import heatshrink
from heatshrink.core import Encoder, Reader, Writer

from .constants import LARGE_PARAGRAPH
from .utils import random_string


class BaseTest(unittest.TestCase):
    def assertNotRaises(self, func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            msg = 'Expected no exception, but got {.__name__}'
            raise AssertionError(msg.format(e.__class__))


class BaseEncoderTest(BaseTest):
    """Tests for the Writer and Reader classes."""
    def test_checks_window_sz2_type(self):
        for cls in (Writer, Reader):
            self.assertRaises(TypeError, cls, window_sz2='a string')
            self.assertRaises(TypeError, cls, window_sz2=lambda x: None)

    def test_checks_window_sz2_within_limits(self):
        for cls in (Writer, Reader):
            self.assertRaises(ValueError, cls, window_sz2=3)
            self.assertRaises(ValueError, cls, window_sz2=16)
            self.assertNotRaises(cls, window_sz2=5)
            self.assertNotRaises(cls, window_sz2=14)

    # TODO: These kind of tests might be redundant
    def test_checks_lookahead_sz2_type(self):
        for cls in (Writer, Reader):
            self.assertRaises(TypeError, cls, lookahead_sz2='a string')
            self.assertRaises(TypeError, cls, lookahead_sz2=lambda x: None)

    def test_checks_lookahead_sz2_within_limits(self):
        for cls in (Writer, Reader):
            self.assertRaises(ValueError, cls, lookahead_sz2=1)
            self.assertRaises(ValueError, cls, lookahead_sz2=16)
            self.assertNotRaises(cls, lookahead_sz2=4)
            self.assertNotRaises(cls, lookahead_sz2=10)


class EncoderTest(BaseTest):
    def setUp(self):
        # TODO: Find a way to test with both reader and writer
        self.encoder = Encoder(Writer())

    def test_fill_accepted_types(self):
        self.assertNotRaises(self.encoder.fill, b'abcde')
        self.assertNotRaises(self.encoder.fill, u'abcde'.encode('utf8'))
        self.assertNotRaises(self.encoder.fill, bytearray([1, 2, 3]))
        self.assertNotRaises(self.encoder.fill, array.array('B', [1, 2, 3]))
        self.assertNotRaises(self.encoder.fill, [1, 2, 3])

        self.assertRaises(TypeError, self.encoder.fill, memoryview(b'abcde'))
        self.assertRaises(TypeError, self.encoder.fill, u'abcde')
        # Obvious fail cases
        self.assertRaises(TypeError, self.encoder.fill, lambda x: x)
        self.assertRaises(TypeError, self.encoder.fill, True)

    def test_finished_true_after_finish(self):
        self.assertFalse(self.encoder.finished)
        self.encoder.finish()
        self.assertTrue(self.encoder.finished)

    def test_operation_after_finish_fails(self):
        self.encoder.fill('abcde')
        self.encoder.finish()
        self.assertRaises(ValueError, self.encoder.fill, 'abcde')
        self.assertRaises(ValueError, self.encoder.finish)


class EncodeFunctionTest(BaseTest):
    """Tests for the core.encode function."""
    def setUp(self):
        self.encoded = heatshrink.encode(b'abcde')

    def test_encoded_size(self):
        self.assertEqual(len(self.encoded), 6)

    def test_encoded_bytes(self):
        self.assertEqual(self.encoded, b'\xb0\xd8\xacvK(')

    def test_encode_with_window_sz2(self):
        encoded = heatshrink.encode(b'abcde', window_sz2=8)
        # FIXME: Prove that this setting changes output
        self.assertEqual(encoded, b'\xb0\xd8\xacvK(')

    def test_encode_with_lookahead_sz2(self):
        encoded = heatshrink.encode(b'abcde', lookahead_sz2=3)
        self.assertEqual(encoded, b'\xb0\xd8\xacvK(')

    def test_different_params_yield_different_output(self):
        string = b'A string with stuff in it'
        self.assertNotEqual(heatshrink.encode(string, window_sz2=8),
                            heatshrink.encode(string, window_sz2=11))
        self.assertNotEqual(heatshrink.encode(string, lookahead_sz2=4),
                            heatshrink.encode(string, lookahead_sz2=8))


class DecodeFunctionTest(BaseTest):
    """Tests for the core.decode function."""

    def test_returns_string(self):
        self.assertIsInstance(heatshrink.decode('abcde'), str)

    def test_decode_with_window_sz2(self):
        decoded = heatshrink.decode(b'\xb0\xd8\xacvK(', window_sz2=11)
        self.assertEqual(decoded, 'abcde')

    def test_decode_with_lookahead_sz2(self):
        decoded = heatshrink.decode('\xb0\xd8\xacvK(', lookahead_sz2=3)
        self.assertEqual(decoded, 'abcde')


class EncoderToDecoderTest(BaseTest):
    """
    Tests assertion that data passed through the encoder
    and then the decoder with the same parameters will be
    equal to the original data.
    """

    def test_round_robin(self):
        encoded = heatshrink.encode(b'a string')
        self.assertEqual(heatshrink.decode(encoded), 'a string')

    def test_with_a_paragraph(self):
        encoded = heatshrink.encode(LARGE_PARAGRAPH)
        self.assertEqual(heatshrink.decode(encoded), LARGE_PARAGRAPH)

    def test_with_large_strings(self):
        test_sizes = [1000, 10000, 100000]

        for size in test_sizes:
            contents = random_string(size)

            decoded = heatshrink.decode(heatshrink.encode(contents))
            # Check whole file, but don't use assertEqual as it will
            # print all the data
            if decoded != contents:
                msg = ('Decoded and original file contents '
                       'do not match for size: {}')
                self.fail(msg.format(size))
