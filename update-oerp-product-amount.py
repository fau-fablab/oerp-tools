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
import sqlite3
from datetime import date
from oerphelper import *
import oerplib

__authors__ = "Patrick Kanzler <patrick.kanzler@fablab.fau.de>"
__license__ = "GPLv3"
__copyright__ = "Copyright (C) 2017 {}".format(__authors__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('update-oerp-product-amount')

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


def print_info(message):
    """ prints a info message to stdout
    """
    logger.info(message)
    print("[i] {}".format(message), file=sys.stdout)


def get_database_handle():
    """ returns a database handle
    """
    database_file = 'snapshotOhnePins.sqlite3'
    logger.debug('connecting to database {}'.format(database_file))
    conn = sqlite3.connect(database_file)
    return conn


def get_products_from_day(conn, dateday):
    """ returns list of (product, quantity) for a day (specified as day)
    """
    c = conn.cursor()

    t = ("{}%".format(dateday.strftime('%Y-%m-%d')),)
    query = "SELECT * FROM position WHERE rechnung in (SELECT id FROM rechnung WHERE datum LIKE ?);"
    logger.debug('searching register-database for products on {}'.format(t))
    queryresult = c.execute(query, t)

    result = []
    for row in queryresult:
        productrow = (row[6], row[2], row[3])
        result.append(productrow)
    logger.debug('found products: {}'.format(result))
    return result


def extract_code_from_db_product(product):
    """ returns the code from the database product
    """
    return product[0]


def get_product_from_code(product_code):
    """ returns the product from the code
    """
    logger.debug('searching prduct with code "{}"'.format(product_code))
    product_id = getId('product.product', [('default_code', '=', product_code)])
    product = read('product.product', product_id, ['name', 'id', 'qty_available', 'type', 'uom_id'])
    logger.debug('found product "{}"'.format(product))
    return product


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
    #TODO in funktion setzen
    conn = get_database_handle()

    get_products_from_day(conn, date(2017,8,17))
    get_products_from_day(conn, date.today())
    get_products_from_day(conn, date(2017,8,14))

    filtered_products = []
    filter_date = date(2017, 8, 14)
    for product in get_products_from_day(conn, filter_date):
        erp_product = get_product_from_code(extract_code_from_db_product(product))
        if erp_product['type'] == 'consu':
            filtered_products.append(erp_product)
    logger.info('filtered products from {} and got: {}'.format(filter_date, filtered_products))




if __name__ == "__main__":
    main()
