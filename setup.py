from setuptools import setup
from Cython.Build import cythonize
from Cython.Distutils import Extension
from os import path
from codecs import open

heatshrink_module = Extension('heatshrink',
                              include_dirs=['.'],
                              extra_compile_args=['-std=c99'],
                              sources=['src/heatshrink.pyx',
                                       'heatshrink/heatshrink_encoder.c',
                                       'heatshrink/heatshrink_decoder.c'])

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(name='Heatshrink',
      version='0.2.2',
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
      ext_modules=cythonize([heatshrink_module]))
