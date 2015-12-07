# -*- coding: utf-8 -*-

"""bustools

Python tools for electrical busses
"""

import os, re, codecs

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

# from https://github.com/pypa/pip/blob/develop/setup.py
def read(*parts):
    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    return codecs.open(os.path.join(here, *parts), 'r').read()

# from https://github.com/pypa/pip/blob/develop/setup.py
def find_version(*file_paths):
    version_file = read(*file_paths)
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                              version_file, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')

setup(
    name = 'bustools',
    version = find_version('bustools', '__init__.py'),
    description = 'Python tools for electrical busses',
    long_description = read('README.rst'),
    url = 'https://github.com/FlyingCampDesign/bustools.git',
    author = 'Flying Camp Design',
    author_email = 'support@flyingcampdesign.com',
    license = 'MIT',
    keywords = 'development embedded I2C SPI',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Embedded Systems',
    ],

    extras_require = {
        'aardvark': ['aardvark_py']
    },

    packages = find_packages(),

    include_package_data = True,
)
