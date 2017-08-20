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
from oerphelper import oerp, getId
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
    query = ("SELECT * FROM position WHERE rechnung in "
             "(SELECT id FROM rechnung WHERE datum LIKE ?);")
    logger.debug('searching register-database for products on {}'.format(t))
    queryresult = c.execute(query, t)

    result = {}
    for row in queryresult:
        if row[6] in result:
            new_amount = result[row[6]][0] + float(row[2])
            result[row[6]] = (new_amount, row[3])
            logger.debug('added new amount {} to entry {}: {}'.format(
                float(row[2]),
                row[6], new_amount
                ))
        else:
            result[row[6]] = (float(row[2]), row[3])
            logger.debug('update dict with {}'.format({
                row[6]: (float(row[2]), row[3])
                }))
    logger.debug('found products: {}'.format(result))
    return result


def get_product_from_code(product_code):
    """ returns the product from the code
    """
    logger.debug('searching product with code "{}"'.format(product_code))
    product_id = getId('product.product',
                       [('default_code', '=', product_code)])

    # product = read('product.product', product_id,
    #        ['default_code', 'name', 'id', 'qty_available', 'type', 'uom_id'])
    # products = searchAndBrowse('product.product', [('default_code', '=', product_code)])

    # for product in products:
    #    print(product)

    product = oerp.browse('product.product', product_id)
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
    # TODO in funktion setzen
    conn = get_database_handle()

    # get_products_from_day(conn, date(2017,8,17))
    # get_products_from_day(conn, date.today())
    # get_products_from_day(conn, date(2017,8,14))

    filtered_products = []
    filter_date = date(2017, 8, 14)
    database_products = get_products_from_day(conn, filter_date)
    logger.info('found products in database: {}'.format(database_products))
    conn.close()

    consu = "consu"
    for product in database_products:
        erp_product = get_product_from_code(product)
        if erp_product.type == consu:
            filtered_products.append(erp_product)
    logger.info('filtered products that are {} from {} and got: {}'.format(
        consu,
        filter_date,
        filtered_products
        ))

    logger.debug('updating list with new quantities')
    for i, product in enumerate(filtered_products):
        product_code = product.default_code
        if product.uom_id.name == database_products[product_code][1]:
            logger.debug('sanity check for {} passed: UOMs are the same ({})'.format(
                product_code,
                product.uom_id.name
                ))
            qty_old = filtered_products[i].qty_available
            qty_update = database_products[product_code][0]
            filtered_products[i].qty_available = qty_old - qty_update
            logger.debug('substracting {} from {}'.format(
                qty_update,
                product_code
                ))
    logger.info('updated qty: {}'.format(filtered_products))

    logger.debug('write new values to OERP')
    for _, product in enumerate(filtered_products):
        p_id = product.id
        p_code = product.default_code
        new_qty = product.qty_available
        # oerp.write_record(product) # das geht so nicht, weil qty_available readonly ist
        no_location = False
        if product.location_id:
            loc_id = product.location_id
        elif (product.categ_id.property_stock_location and
              product.categ_id.property_stock_location.id):
            loc_id = product.categ_id.property_stock_location.id
        else:
            no_location = True

        if not no_location:
            try:
                change_id = oerp.execute_kw('stock.change.product.qty',
                                            'create', [{
                                                        'product_id': p_id,
                                                        'location_id': loc_id,
                                                        'new_quantity': new_qty,
                                                        }])
                print(change_id)
                oerp.execute('stock.change.product.qty',
                             'change_product_qty', [change_id, ])
                # oerp.execute_kw('stock.change.product.qty', 'change_product_qty', [{'product_id': p_id, 'location_id': location_id, 'new_quantity': new_qty}], context=oerpContext)
                # oerp.execute_kw('stock.change.product.qty', 'change_product_qty')
            except oerplib.error.RPCError as e:
                print(e)
                print(e[1])
                # print(e.message)
                # print(e.oerp_traceback)
            logger.info('update product {} with qty {}'.format(
                p_code,
                new_qty
                ))
        else:
            logger.info('Code {} has no location! Cannot update!'.format(
                p_code
                ))
    logger.debug('done')


if __name__ == "__main__":
    main()
