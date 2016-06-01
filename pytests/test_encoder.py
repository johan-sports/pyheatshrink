import unittest

import array
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
        string_size = 100000
        rand_string = ''.join(random.choice(string.lowercase)
                              for _ in range(string_size))
        start_time = time.time()
        # Just test that it doesn't fail
        heatshrink.encode(rand_string)
        print('\n--- encoded {} bytes in {} seconds ---'
              .format(string_size, time.time() - start_time))


# import sys
# import heatshrink

# if __name__ == '__main__':
#     filename = sys.argv[1]

#     with open(filename, 'rb') as f:
#         data = f.read()
#         print('Uncompressed size: {}'.format(len(data)))

#         encoded_data = heatshrink.encode(data)
#         print('Compressed size: {}'.format(encoded_data.shape[0]))

#         print('Running memoryview checks:')
#         print('\t==> Running .tobytes()')
#         encoded_data.tobytes()
#         print('\t==> Running .tolist()')
#         encoded_data.tolist()
#         print('\t==> Copying memoryview')
#         copied_data = encoded_data[:]
#         print('\t==> Deleting original reference')
#         del encoded_data
#         print('\t==> Running .tobytes() on copy')
#         copied_data.tobytes()
#         print('\t==> Running .tolist() on copy')
#         copied_data.tolist()

#         print('Decompressing data...')
#         decoded_data = heatshrink.decode(copied_data)
#         print('Decompressed size: {}'.format(len(decoded_data)))
