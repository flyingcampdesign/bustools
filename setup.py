import bustools

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='bustools',
    version=bustools.__version__,
    author='Flying Camp Design',
    author_email='support@flyingcampdesign.com',
    url='https://github.com/FlyingCampDesign/bustools',
    description="Python tools/wrappers for electrical busses",
    long_description=open('README.rst').read(),
    license='BSD',
    platforms='any',
    packages=[
        'bustools',
    ],
)
