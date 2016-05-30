from distutils.core import setup, Extension

heatshrink_module = Extension('heatshrink',
                              include_dirs=['./heatshrink', './src'],
                              define_macros=[('HEATSHRINK_DEBUGGING_LOGS', '1')],
                              undef_macros=['NDEBUG'],
                              sources=['src/heatshrink.c',
                                       'src/dynamic_arrays.c',
                                       'heatshrink/heatshrink_encoder.c',
                                       'heatshrink/heatshrink_decoder.c'])

setup(name='Heatshrink',
      version='0.1',
      description='Python bindings to the heatshrink library',
      author='JOHAN Sports',
      author_email='antonis@johan-sports.com',
      ext_modules=[heatshrink_module])
