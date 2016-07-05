import unittest

import random
import string
import time

import heatshrink


class EncoderTest(unittest.TestCase):
    def setUp(self):
        self.encoded = heatshrink.encode('abcde')

    def test_encoded_size(self):
        self.assertEqual(self.encoded.shape[0], 6)

    def test_encoded_bytes(self):
        self.assertEqual(self.encoded.tobytes(), '\xb0\xd8\xacvK(')

    def test_encode_with_window_sz2(self):
        encoded = heatshrink.encode('abcde', window_sz2=8)
        # FIXME: Prove that this setting changes output
        self.assertEqual(encoded.tobytes(), b'\xb0\xd8\xacvK(')

    def test_encode_checks_window_sz2_type(self):
        with self.assertRaises(TypeError):
            heatshrink.encode('abcde', window_sz2='a string')
        with self.assertRaises(TypeError):
            heatshrink.encode('abcde', window_sz2=2.123)

    def test_encode_handles_window_sz2_overflow(self):
        with self.assertRaises(OverflowError):
            heatshrink.encode('abcde', window_sz2=256)
        with self.assertRaises(OverflowError):
            heatshrink.encode('abcde', window_sz2=1000)
        with self.assertRaises(OverflowError):
            heatshrink.encode('abcde', window_sz2=-1)

    def test_encode_checks_window_sz2_within_limits(self):
        with self.assertRaises(ValueError):
            heatshrink.encode('abcde', window_sz2=3)
        with self.assertRaises(ValueError):
            heatshrink.encode('abcde', window_sz2=16)
        heatshrink.encode('abcde', window_sz2=5)
        heatshrink.encode('abcde', window_sz2=14)

    def test_encode_with_lookahead_sz2(self):
        encoded = heatshrink.encode('abcde', lookahead_sz2=3)
        self.assertEqual(encoded.tobytes(), b'\xb0\xd8\xacvK(')

    def test_encode_checks_lookahead_sz2_type(self):
        with self.assertRaises(TypeError):
            heatshrink.encode('abcde', lookahead_sz2='a string')
        with self.assertRaises(TypeError):
            heatshrink.encode('abcde', lookahead_sz2=2.123)

    def test_encode_handles_lookahead_sz2_overflow(self):
        with self.assertRaises(OverflowError):
            heatshrink.encode('abcde', lookahead_sz2=256)
        with self.assertRaises(OverflowError):
            heatshrink.encode('abcde', lookahead_sz2=1000)
        with self.assertRaises(OverflowError):
            heatshrink.encode('abcde', lookahead_sz2=-1)

    def test_encode_checks_lookahead_sz2_within_limits(self):
        with self.assertRaises(ValueError):
            heatshrink.encode('abcde', lookahead_sz2=1)
        with self.assertRaises(ValueError):
            heatshrink.encode('abcde', lookahead_sz2=16)
        heatshrink.encode('abcde', lookahead_sz2=4)
        heatshrink.encode('abcde', lookahead_sz2=10)

    def test_encoded_format(self):
        self.assertEqual(self.encoded.format, 'B')

    def test_encoded_type(self):
        self.assertIsInstance(self.encoded, memoryview)

    def test_encoded_dimensions(self):
        self.assertEqual(self.encoded.ndim, 1)

    def test_encoded_readonly(self):
        self.assertEqual(self.encoded.readonly, True)

    def test_valid_encode_types(self):
        heatshrink.encode('abcde')
        heatshrink.encode(bytes('abcde'))
        heatshrink.encode(unicode('abcde'))
        # TODO: Also get this to work with ByteIO and other
        # TODO: buffer compatible objects.
        # heatshrink.encode(memoryview(b'abcde'))
        # heatshrink.encode(bytearray([1, 2, 3]))
        # heatshrink.encode(array.array('B', [1, 2, 3]))
        with self.assertRaises(TypeError):
            heatshrink.encode([1, 2, 3])
            heatshrink.encode(lambda x: x)
            heatshrink.encode(True)

    def test_encoded_can_be_copied(self):
        copied = self.encoded[:]
        self.assertEqual(copied, self.encoded)
        self.assertIsNot(copied, self.encoded)  # Different identity
        del self.encoded
        # Ensure everything still works
        self.assertEqual(copied.tobytes(), '\xb0\xd8\xacvK(')


class DecoderTest(unittest.TestCase):
    def test_returns_string(self):
        self.assertIsInstance(heatshrink.decode('abcde'), str)

    def test_accepts_buffer_like_objects(self):
        heatshrink.decode('abcde')
        heatshrink.decode(b'abcde')
        # heatshrink.decode(u'abcde')
        heatshrink.decode(bytearray([1, 2, 3]))
        # heatshrink.decode(array.array('B', [1, 2, 3]))
        heatshrink.decode(memoryview(b'abcde'))
        with self.assertRaisesRegexp(TypeError, ".*buffer protocol.*"):
            heatshrink.decode([1, 2, 3])
            heatshrink.decode(1)
            heatshrink.decode(lambda x: x)
            heatshrink.decode(True)

    def test_decode_with_window_sz2(self):
        decoded = heatshrink.decode(b'\xb0\xd8\xacvK(', window_sz2=11)
        self.assertEqual(decoded, 'abcde')

    def test_decode_checks_window_sz2_type(self):
        with self.assertRaises(TypeError):
            heatshrink.decode('abcde', window_sz2='a string')
        with self.assertRaises(TypeError):
            heatshrink.decode('abcde', window_sz2=2.123)

    def test_decode_handles_window_sz2_overflow(self):
        with self.assertRaises(OverflowError):
            heatshrink.decode('abcde', window_sz2=256)
        with self.assertRaises(OverflowError):
            heatshrink.decode('abcde', window_sz2=1000)
        with self.assertRaises(OverflowError):
            heatshrink.decode('abcde', window_sz2=-1)

    def test_decode_checks_window_sz2_within_limits(self):
        with self.assertRaises(ValueError):
            heatshrink.decode('abcde', window_sz2=3)
        with self.assertRaises(ValueError):
            heatshrink.decode('abcde', window_sz2=16)
        heatshrink.decode('abcde', window_sz2=5)
        heatshrink.decode('abcde', window_sz2=14)

    def test_decode_with_lookahead_sz2(self):
        decoded = heatshrink.decode('\xb0\xd8\xacvK(', lookahead_sz2=3)
        self.assertEqual(decoded, 'abcde')

    def test_decode_checks_lookahead_sz2_type(self):
        with self.assertRaises(TypeError):
            heatshrink.decode('abcde', lookahead_sz2='a string')
        with self.assertRaises(TypeError):
            heatshrink.decode('abcde', lookahead_sz2=2.123)

    def test_decode_handles_lookahead_sz2_overflow(self):
        with self.assertRaises(OverflowError):
            heatshrink.decode('abcde', lookahead_sz2=256)
        with self.assertRaises(OverflowError):
            heatshrink.decode('abcde', lookahead_sz2=1000)
        with self.assertRaises(OverflowError):
            heatshrink.decode('abcde', lookahead_sz2=-1)

    def test_decode_checks_lookahead_sz2_within_limits(self):
        with self.assertRaises(ValueError):
            heatshrink.decode('abcde', lookahead_sz2=1)
        with self.assertRaises(ValueError):
            heatshrink.decode('abcde', lookahead_sz2=16)
        heatshrink.decode('abcde', lookahead_sz2=4)
        heatshrink.decode('abcde', lookahead_sz2=10)




class EncoderToDecoderTest(unittest.TestCase):
    def test_encoder_output_to_decoder_valid(self):
        encoded = heatshrink.encode(b'a string')
        self.assertEqual(heatshrink.decode(encoded), 'a string')
