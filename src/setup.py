#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='oerp-tools',
    version='1.0.0',
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    url='https://github.com/fau-fablab/oerp-tools',
    license='CC BY-SA 4.0',
    author='FAU FabLab',
    author_email='kontakt@fablab.fau.de',
    description='Hacky commandlinetools for things that should rather be OERP plugins',
    long_description=long_description,
    install_requires=['ConfigParser', 'argcomplete', 'argparse', 'oerplib', 'docopt'],
)
