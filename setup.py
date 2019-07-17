import codecs
from os.path import dirname, join, abspath

from setuptools import setup, find_packages

here = abspath(dirname(__file__))


def read(*parts):
    return codecs.open(join(here, *parts), 'r', encoding='utf-8').read()


def find_version(package):
    about = {}
    exec(read(package, '__version__.py'), about)
    return about['__version__']


setup(
    name='nv',
    version=find_version('nv'),

    maintainer="Nathan Muir",
    maintainer_email="ndmuir@gmail.com",

    url='https://github.com/3stack-software/nv',

    license='Apache2',
    description='A utility for managing multiple configurations & environments',
    long_description='\n' + read('README.rst'),

    packages=find_packages(exclude=('tests',)),

    python_requires='>= 3.6',

    setup_requires=[],
    install_requires=[
        'sh',
        'boto3',
        'click',
        'cryptography',
        'keyring',
    ],
    entry_points={
        'console_scripts': [
            'nv = nv.cli:main'
        ]
    },
    classifiers=[
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
)
