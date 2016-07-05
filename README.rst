PyHeatshrink
============

Python binding to the `heatshrink LZSS compression
library <https://github.com/atomicobject/heatshrink>`__.

| *Supported versions:*
| Python >= 2.6

| Note: Python 3 support is experimental.

Installation
------------

::

    $ python setup.py install

Usage
-----

The encoder accepts any object which implements the read-only buffer
interface and returns a memoryview containing unsigned bytes.

::

    >>> import heatshrink
    >>> mem = heatshrink.encode('a string')
    >>> type(mem)
    <type 'memoryview'>
    >>> mem.tobytes()
    '\xb0\xc8.wK\x95\xa6\xddg'
    >> mem.format
    'B'

The decoder accepts any object that implements the buffer protocol and
returns a byte representation of the decoded data.

::

    >>> import heatshrink
    >>> mem = memoryview(b'\xb0\xc8.wK\x95\xa6\xddg')
    >>> heatshrink.decode(mem)
    'a string'
    >>> heatshrink.decode(b'\xb0\xc8.wK\x95\xa6\xddg')
    'a string'

Both the encoder and decoder allow providing :code:`window_sz2` and :code:`lookahead_sz2` keywords:

:code:`window_sz2` - The window size determines how far back in the input can be searched for repeated patterns. A window_sz2 of 8 will only use 256 bytes (2^8), while a window_sz2 of 10 will use 1024 bytes (2^10). The latter uses more memory, but may also compress more effectively by detecting more repetition.

:code:`lookahead_sz2` - The lookahead size determines the max length for repeated patterns that are found. If the lookahead_sz2 is 4, a 50-byte run of 'a' characters will be represented as several repeated 16-byte patterns (2^4 is 16), whereas a larger lookahead_sz2 may be able to represent it all at once. The number of bits used for the lookahead size is fixed, so an overly large lookahead size can reduce compression by adding unused size bits to small patterns.


Check out the `heatshrink configuration page <https://github.com/atomicobject/heatshrink#configuration>`__ for more details.


For more use cases, please refer to `pytests.py <pytests.py>`__.

Benchmarks
----------

The benchmarks check compression/decompression against a ~6MB file:

::
   $ python bench/benchmarks.py

Testing
-------

CMake + CMocka is used for generating unit tests. To build run:

::

    $ mkdir build && cd build
    $ cmake ..
    $ make
    $ make test

License
-------

ISC license
