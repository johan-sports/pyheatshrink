from distutils.core import setup, Extension

heatshrink_module = Extension('heatshrink',
                              sources=['heatshrink.c'])

setup(name='Heatshrink',
      version='0.1',
      description='Python bindings to the heatshrink library',
      author='JOHAN Sports',
      author_email='antonis@johan-sports.com',
      ext_modules=[heatshrink_module])
