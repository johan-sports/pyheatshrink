from os import path
from codecs import open
from setuptools import setup, Extension

try:
    from Cython.Build import cythonize
except ImportError:
    USE_CYTHON = False
else:
    USE_CYTHON = True


# Compiled file extension to use. If we're not using Cython,
# just use the plain C file.
EXT = '.pyx' if USE_CYTHON else '.c'

heatshrink_module = Extension('heatshrink.core',
                              include_dirs=['.', './heatshrink/_heatshrink'],
                              extra_compile_args=['-std=c99'],
                              sources=['heatshrink/core' + EXT,
                                       'heatshrink/_heatshrink/heatshrink_encoder.c',
                                       'heatshrink/_heatshrink/heatshrink_decoder.c'])

if USE_CYTHON:
    extensions = cythonize([heatshrink_module])
else:
    extensions = [heatshrink_module]


here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='Heatshrink',
      version='0.2.4',
      # Author details
      author='Antonis Kalou @ JOHAN Sports',
      author_email='antonis@johan-sports.com',
      # Project details
      description='Python bindings to the heatshrink library',
      long_description=long_description,
      url='https://github.com/johan-sports/pyheatshrink',
      license='ISC',

      classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: System :: Archiving :: Compression',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: ISC License (ISCL)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
      ],

      keywords='compression bindings heatshrink LZSS',
      test_suite="tests",
      packages=['heatshrink'],
      ext_modules=extensions)
