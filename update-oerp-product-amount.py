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
from ConfigParser import ConfigParser

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


cfg = ConfigParser({'anonymous_partner_id': 87})

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


def get_invoices_from_day(conn, dateday):
    """ returns all invoices on a certain day
    """
    c = conn.cursor()

    t = ("{}%".format(dateday.strftime('%Y-%m-%d')),)
    query = ("SELECT id FROM rechnung WHERE datum LIKE ?;")
    logger.debug('searching all invoices on {}'.format(t))
    queryresult = c.execute(query, t)

    result = {}
    for id in queryresult:
        invoice = "{}".format(id[0])
        result[invoice] = get_products_from_invoice_number(conn, invoice)
    logger.debug('found invoices {}'.format(result))
    return result


def get_products_from_invoice_number(conn, invoice):
    """ returns all products in an invoice
    """
    c = conn.cursor()

    query = ("SELECT * FROM position WHERE rechnung is ?;")
    logger.debug('searching register-database for products on invoice {}'.format(invoice))
    queryresult = c.execute(query, (invoice, ))
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
    logger.debug("found the these products on invoice {}: {}".format(
        invoice,
        result,
        ))
    return result


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
    filter_date = date.today()
    database_products = get_products_from_day(conn, filter_date)
    database_invoices = get_invoices_from_day(conn, filter_date)
    logger.info('found products in database: {}'.format(database_products))
    conn.close()

    #TODO pay_journal_id =
    pay_journal_id = 8
    #TODO unterscheidung für FAUcard und Bargeld

    try:
        for invoice in database_invoices:
            logger.info('parsing invoice {}'.format(invoice))
            #TODO partner_id = cfg.getint('anonymous_partner_id')
            partner_id = 87
            order_data = oerp.execute('sale.order', 'onchange_partner_id', [], partner_id)
            logger.debug(order_data)
            #assert not order_data['warning'], print_error("failed getting default values for sale.order")
            order_data = order_data['value']
            invoice_line = 'RN Kasse {}'.format(invoice)
            order_data.update({'partner_id': partner_id,
                               'order_policy': 'manual',
                               'picking_policy': 'one',
                               'client_order_ref': invoice_line})
            order_id = oerp.create('sale.order', order_data)
            logger.debug('created order {}'.format(order_id))

            for product_code in database_invoices[invoice]:
                logger.debug('parsing product {}'.format(product_code))
                product_qty = database_invoices[invoice][product_code][0]
                product_id = get_product_from_code(product_code).id
                order_line_data = oerp.execute(
                        'sale.order.line', 'product_id_change', [],
                        order_data['pricelist_id'], product_id, product_qty,
                        # UOM  qty_uos UOS    Name   partner_id
                        False, 0, False, '',  partner_id)['value']
                order_line_data.update({'order_id': order_id, 'product_id': product_id,
                        'product_uom_qty': product_qty})
                logger.debug(order_line_data)
                order_line_id = oerp.create('sale.order.line', order_line_data)
                logger.debug('created order line {}'.format(order_line_id))
            logger.debug('finishing sale order {}'.format(invoice))
            oerp.exec_workflow('sale.order', 'order_confirm', order_id)
            picking_id = oerp.read('sale.order', order_id, ['picking_ids'])['picking_ids']
            if picking_id:
                # No picking list is created if only services are bought
                picking_id = picking_id[0]
                oerp.write('stock.picking.out', picking_id, {'auto_picking': True})

            invoice_id = oerp.execute('sale.order', 'action_invoice_create', [order_id])
            oerp.exec_workflow('account.invoice', 'invoice_open', invoice_id)

            logger.debug('finishing payment')
            #TODO cash, faucard und kassenbuch trennen (weil zB kassenbuch sonst doppelt verbucht wird)
            current_period = oerp.execute('account.period', 'find')[0]
            pay_account_id = oerp.read(
                    'account.journal',
                    pay_journal_id,
                    ['default_debit_account_id'])['default_debit_account_id'][0]

            oerp.execute('account.invoice', 'pay_and_reconcile',
                    [invoice_id],
                    False,
                    pay_account_id, current_period, pay_journal_id,
                    False, False, False,
                    oerp.context)

            paid = oerp.read('account.invoice', invoice_id, ['state'])['state'] == 'paid'
            oerp.execute('sale.order', 'action_done', order_id)
    except oerplib.error.RPCError as e:
        print_error(e[1])
    logger.info('done!')


if __name__ == "__main__":
    main()
