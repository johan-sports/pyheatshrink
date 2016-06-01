from setuptools import setup, Extension

heatshrink_module = Extension('heatshrink',
                              include_dirs=['.', './src'],
                              sources=['src/heatshrink.c',
                                       'src/dynamic_arrays.c',
                                       'heatshrink/heatshrink_encoder.c',
                                       'heatshrink/heatshrink_decoder.c'])

setup(name='Heatshrink',
      version='0.1.0',
      description='Python bindings to the heatshrink library',
      author='JOHAN Sports',
      author_email='antonis@johan-sports.com',
      test_suite="pytests.test_encoder",
      zip_safe=False,
      ext_modules=[heatshrink_module])
