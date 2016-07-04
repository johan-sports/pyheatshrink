import unittest

import random
import string
import time

import heatshrink


class EncoderTest(unittest.TestCase):
    def setUp(self):
        self.encoded = heatshrink.encode('abcde')

    def test_encoded_size(self):
        self.assertEqual(self.encoded.shape[0], 6L)

    def test_encoded_bytes(self):
        self.assertEqual(self.encoded.tobytes(), '\xb0\xd8\xacvK(')

    def test_encode_with_window_size(self):
        encoded = heatshrink.encode('abcde', window_size=8)
        # FIXME: Prove that this setting changes output
        self.assertEqual(encoded.tobytes(), b'\xb0\xd8\xacvK(')

    def test_encode_checks_window_size_type(self):
        with self.assertRaises(TypeError):
            heatshrink.encode('abcde', window_size='a string')
        with self.assertRaises(TypeError):
            heatshrink.encode('abcde', window_size=2.123)

    def test_encode_checks_window_size_within_limits(self):
        with self.assertRaises(ValueError):
            heatshrink.encode('abcde', window_size=3)
        with self.assertRaises(ValueError):
            heatshrink.encode('abcde', window_size=16)
        heatshrink.encode('abcde', window_size=4)
        heatshrink.encode('abcde', window_size=15)

    def test_encode_with_lookahead_size(self):
        encoded = heatshrink.encode('abcde', lookahead_size=2)
        self.assertEqual(encoded.tobytes(), b'\xb0\xd8\xacvK(')

    def test_encode_checks_lookahead_size_type(self):
        with self.assertRaises(TypeError):
            heatshrink.encode('abcde', lookahead_size='a string')
        with self.assertRaises(TypeError):
            heatshrink.encode('abcde', lookahead_size=2.123)

    def test_encode_checks_lookahead_size_within_limits(self):
        with self.assertRaises(ValueError):
            heatshrink.encode('abcde', lookahead_size=1)
        with self.assertRaises(ValueError):
            heatshrink.encode('abcde', lookahead_size=16)
        heatshrink.encode('abcde', lookahead_size=4)
        heatshrink.encode('abcde', lookahead_size=10)

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

    # TODO: Move me to a benchmark
    def test_encode_large_strings(self):
        string_size = 50000
        rand_string = ''.join(random.choice(string.lowercase)
                              for _ in range(string_size))
        start_time = time.time()
        # Just test that it doesn't fail
        heatshrink.encode(rand_string)
        print('\n--- encoded {} bytes in {} seconds ---'
              .format(string_size, time.time() - start_time))


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


class EncoderToDecoderTest(unittest.TestCase):
    def test_encoder_output_to_decoder_valid(self):
        encoded = heatshrink.encode(b'a string')
        self.assertEqual(heatshrink.decode(encoded), 'a string')
