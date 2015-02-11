#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# Copyright (C) 2015 Max Gaukler <max@fablab.fau.de>
# 
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU
# General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with this program. If not,
# see <http://www.gnu.org/licenses/>.

"""set a purchase order as "done"

Usage:
  setOrderDone.py PO000123... [--force]
  
Options:
  --force             still continue even if the script says something is not good
  -h --help     Show this screen.

order can be PO00123 

"""

from oerphelper import *
import sys
from docopt import docopt
try:
    from termcolor import colored
except ImportError:
    sys.stderr.write("termcolor not found. please: sudo pip install termcolor\n")
    def colored(s, c=None, attrs=None):
        print s

def printError(s):
    print colored(s, 'red',  attrs=['bold'])

def printBold(s):
    print colored(s, 'blue',  attrs=['bold'])

arguments = docopt(__doc__)
force = arguments['--force']
for po in arguments['PO000123']:
    problem=False
    po=po.upper()
    if not po.startswith("PO"):
        printError("Error: order number must start with PO...")
        print __doc__
        sys.exit(1)
    printBold("Order: {}".format(po))
    order=getId('purchase.order', [('name', '=', po)])
    order=oerp.browse('purchase.order', order)
    if order.state=="done":
        printError("already marked done.")
        continue
    if not order.state=="approved":
        printError("order state is not 'approved'")
        if not force:
            problem=True
    
    # check invoice==paid
    invoicesOkay=True
    invoices=list(order.invoice_ids)
    if len(invoices)==0:
        print ""
        problem=True
    for inv in order.invoice_ids:
        if inv.state != 'paid':
            printError("Invoice is not paid")
            invoicesOkay=False
    if not invoicesOkay:
        problem=True
    
    pickingOkay=True
    for pick in order.picking_ids:
        print "checking picking {}".format(pick.name)
        if pick.invoice_state=='none':
            print "Warning: invoice creation is not 'from picking list' (e.g. prepaid). This script cannot check if only for some part of the articles an invoice was created and paid."
        if pick.invoice_state == '2binvoiced':
            printError("picking list is still to-be-invoiced")
            problem=True
        if pick.state != 'done':
            printError("picking list is not done, but in state '{}'".format(pick.state))
            problem=True
    if (not problem) or force:
        print "marking as done\n"
        order.state='done'
        oerp.write_record(order)
    else:
        print "skipping. to ignore errors, use --force"
    


sys.exit(0)
