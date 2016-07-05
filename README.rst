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

For more use cases, please refer to `pytests.py <pytests.py>`__.

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
