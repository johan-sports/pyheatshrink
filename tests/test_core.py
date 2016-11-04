import array
import unittest

import heatshrink
from heatshrink.core import Encoder, Reader, Writer

from .constants import LARGE_PARAGRAPH
from .utils import random_string


class TestUtils(object):
    """Mixin that provides extra testing utilities."""

    def assertNotRaises(self, func, *args, **kwargs):
        """Ensure that the an exception isn't raised.

        An AssertionError is raised if calling func with
        the given argument triggers any exception.
        """
        try:
            func(*args, **kwargs)
        except Exception as e:
            msg = 'Expected no exception, but got {.__name__}'
            raise AssertionError(msg.format(e.__class__))


class InternalEncodersTest(TestUtils, unittest.TestCase):
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


class EncoderTest(TestUtils, unittest.TestCase):
    """Test encoder state machine."""

    def setUp(self):
        self.reader = Reader()
        self.writer = Writer()
        self.encoders = [Encoder(e) for e in [self.reader, self.writer]]

    def test_fill_accepted_types(self):
        for encoder in self.encoders:
            self.assertNotRaises(encoder.fill, b'abcde')
            self.assertNotRaises(encoder.fill, u'abcde'.encode('utf8'))
            self.assertNotRaises(encoder.fill, bytearray([1, 2, 3]))
            self.assertNotRaises(encoder.fill, array.array('B', [1, 2, 3]))
            self.assertNotRaises(encoder.fill, [1, 2, 3])

            self.assertRaises(TypeError, encoder.fill, memoryview(b'abcde'))
            self.assertRaises(TypeError, encoder.fill, u'abcde')
            # Obvious fail cases
            self.assertRaises(TypeError, encoder.fill, lambda x: x)
            self.assertRaises(TypeError, encoder.fill, True)

    def test_finished_true_after_finish(self):
        for encoder in self.encoders:
            self.assertTrue(not encoder.finished)
            encoder.finish()
            self.assertTrue(encoder.finished)

    def test_operation_after_finish_fails(self):
        for encoder in self.encoders:
            encoder.fill('abcde')
            encoder.finish()
            self.assertRaises(ValueError, encoder.fill, 'abcde')
            self.assertRaises(ValueError, encoder.finish)

    def test_fill_doesnt_flush_small_values(self):
        encoder = Encoder(self.writer)
        # Pass a small value, this wont cause the encoder
        # to actually do anything
        encoded = encoder.fill('abcde')
        self.assertTrue(len(encoded) == 0)
        # This should clear the encoder completely
        encoded = encoder.finish()
        self.assertTrue(len(encoded) > 0)


class EncodeFunctionTest(TestUtils, unittest.TestCase):
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


class DecodeFunctionTest(TestUtils, unittest.TestCase):
    """Tests for the core.decode function."""

    def test_returns_string(self):
        self.assertIsInstance(heatshrink.decode('abcde'), str)

    def test_decode_with_window_sz2(self):
        decoded = heatshrink.decode(b'\xb0\xd8\xacvK(', window_sz2=11)
        self.assertEqual(decoded, 'abcde')

    def test_decode_with_lookahead_sz2(self):
        decoded = heatshrink.decode('\xb0\xd8\xacvK(', lookahead_sz2=3)
        self.assertEqual(decoded, 'abcde')


class EncoderToDecoderTest(TestUtils, unittest.TestCase):
    """
    Tests assertion that data passed through the encoder
    and then the decoder with the same parameters will be
    equal to the original data.
    """

    def test_round_trip(self):
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
