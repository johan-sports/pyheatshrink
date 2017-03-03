============
PyHeatshrink
============

Python binding to the `heatshrink LZSS compression
library <https://github.com/atomicobject/heatshrink>`__.

| **Supported versions:**
| Python >= 2.6 -- Full
| Python 3 -- Experimental
| 
| **Tested platforms:**
| * OS X > 10.10
| * Debian 8
| * FreeBSD 10

.. image:: https://travis-ci.org/johan-sports/pyheatshrink.svg?branch=master
    :target: https://travis-ci.org/johan-sports/pyheatshrink

************
Installation
************

From PyPI:

::

   $ easy_install heatshrink
   $ pip install heatshrink

Manual installation:

::

    $ python setup.py install

*****
Usage
*****

Files/Streams
=============

The file interface attempts to imitate the behaviour of the built-in `file` object
and other file-like objects (E.g. :code:`bz2.BZ2File`), thus you can expect all methods
implemented in :code:`file` to also be available.

You can open a heatshrink file by using the :code:`open` function:

::

    >>> import heatshrink
    >>> with heatshrink.open('data.bin', mode='wb') as fp:
    ...     fp.write("Is there anybody in there?")

You can also use :code:`EncodedFile` directly:

::

    >>> from heatshrink import EncodedFile
    >>> with EncodedFile('data.bin') as fp:
    ...     # Read a buffer
    ...     print('Buffered: %r' % fp.read(256))
    ...     # Iterate through lines
    ...     for line in fp:
    ...         print('Read line: %r' % line)
   

Byte strings
============

The encoder accepts any iterable and returns a byte string
containing encoded (compressed) data. 

::

    >>> import heatshrink
    >>> encoded = heatshrink.encode('a string')
    >>> type(encoded)
    <type 'str'>  # <class 'bytes'> in Python 3
    >>> encoded
    '\xb0\xc8.wK\x95\xa6\xddg'

The decoder accepts any object that implements the buffer protocol and
returns a byte representation of the decoded data.

::

    >>> import heatshrink
    >>> decoded = heatshrink.decode(b'\xb0\xc8.wK\x95\xa6\xddg')
    >>> type(decoded)
    <type 'str'>  # <class 'bytes'> in Python 3
    >>> decoded
    'a string'

Parameters
==========

Both the encoder and decoder allow providing :code:`window_sz2` and :code:`lookahead_sz2` keywords:

:code:`window_sz2` - The window size determines how far back in the input can be searched for repeated patterns. A window_sz2 of 8 will only use 256 bytes (2^8), while a window_sz2 of 10 will use 1024 bytes (2^10). The latter uses more memory, but may also compress more effectively by detecting more repetition.

:code:`lookahead_sz2` - The lookahead size determines the max length for repeated patterns that are found. If the lookahead_sz2 is 4, a 50-byte run of 'a' characters will be represented as several repeated 16-byte patterns (2^4 is 16), whereas a larger lookahead_sz2 may be able to represent it all at once. The number of bits used for the lookahead size is fixed, so an overly large lookahead size can reduce compression by adding unused size bits to small patterns.

:code:`input_buffer_size` - How large an input buffer to use for the decoder. This impacts how much work the decoder can do in a single step, and a larger buffer will use more memory. An extremely small buffer (say, 1 byte) will add overhead due to lots of suspend/resume function calls, but should not change how well data compresses.


Check out the `heatshrink configuration page <https://github.com/atomicobject/heatshrink#configuration>`__ for more details.


For more use cases, please refer to the `tests folder <https://github.com/johan-sports/pyheatshrink/blob/master/tests>`__.

**********
Benchmarks
**********

The benchmarks check compression/decompression against a ~6MB file:

::

   $ python bench/benchmarks.py

*******
Testing
*******

Running tests is as simple as doing:

::

    $ python setup.py test

*******
License
*******

ISC license
