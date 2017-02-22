import codecs
from os.path import dirname, join

from setuptools import setup, find_packages

here = dirname(__file__)


def read(*parts):
    return codecs.open(join(here, *parts), 'r').read()


def find_version(*file_paths):
    version = read(*file_paths).strip()
    if version == '':
        raise RuntimeError('No version found')
    return version


def read_markdown(*file_paths):
    try:
        import pandoc.core
        doc = pandoc.core.Document()
        doc.markdown = read(*file_paths)
        return doc.rst
    except ImportError:
        return ''


setup(
    name='nv',
    version=find_version('nv', 'VERSION'),

    maintainer="Nathan Muir",
    maintainer_email="ndmuir@gmail.com",

    url='https://github.com/3stack-software/nv',

    license='Apache2',
    description='A utility for managing multiple configurations & environments',

    packages=find_packages(exclude=('tests',)),

    package_data={
        'nv': ['VERSION']
    },

    setup_requires=[],
    install_requires=[
        'sh',
        'boto3',
        'click',
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
)
