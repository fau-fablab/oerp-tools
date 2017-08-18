#!/usr/bin/python
#  -*- coding: utf-8 -*-
""" Update OERP product amount

This script updates the product quantities in OERP based on a database
snapshot of our cash register.

:author: `Patrick Kanzler <patrick.kanzler@fablab.fau.de>`_
:organization: `FAU FabLab <https://fablab.fau.de>`_
:copyright: Copyright (c) 2017 FAU FabLab
:license: GPLv3
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging
import argparse
import sys

__authors__ = "Patrick Kanzler <patrick.kanzler@fablab.fau.de>"
__license__ = "GPLv3"
__copyright__ = "Copyright (C) 2017 {}".format(__authors__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug('initializing logger')

try:
    from argcomplete import autocomplete
except ImportError:
    def autocomplete_wrapper(*args):
        print_error("Consider installing argcomplete")
    autocomplete = autocomplete_wrapper


def print_error(message):
    """ prints an error message to stderr
    """
    logger.error(message)
    print("[!] {}".format(message), file=sys.stderr)


def parse_args():
    """
    Parses the command line arguments and returns them in an object
    """
    parser = argparse.ArgumentParser(description=__doc__)

    autocomplete(parser)

    args = parser.parse_args()
    return args


def main():
    args = parse_args()


if __name__ == "__main__":
    main()
