#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014  Maximilian Gaukler <max@fablab.fau.de>
# Julian Hammer <julian.hammer@fablab.fau.de>
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


"""export from OERP

Usage:
  export.py purchase.order --shop=<shopname> [--format=<fmt>]
  export.py purchase.order <id> ... [--format=<fmt>]
  
Options:
  --format=<fmt>     Exportformat (auto, csv, tsv) [default: auto]

More info:
  <id> can be both 123 or PO00123
"""
from docopt import docopt

arguments = docopt(__doc__, version='Kassenbuch 1.0')
from oerphelper import *

# export openERP -> csv


# get the right formatting string based on format argument and shop
def get_formatstring(fmt, shop):
    # auto format
    if fmt not in ["csv", "tsv"]:
        if shop == "reichelt.de":
            fmt = "csv"
        else:
            fmt = "tsv"

    if fmt == "tsv":
        return "{qty}\t{code}"
    else:  # csv
        return "{qty};{code}"


# make integer if it is a n.0000 float
def int_format(x):
    if int(x) == x:
        return int(x)
    else:
        return x


if arguments["purchase.order"]:
    search_filter = []

    # filter for shop name, if given
    if arguments["--shop"]:
        shop_id = partnerIdFromName(arguments["--shop"])
        search_filter += [("partner_id", "=", shop_id)]

    # filter for id, if given
    ids = False
    if arguments.get("<id>"):
        # accept both PO01234 and 123 type ids
        ids = [int(x.strip("PO")) for x in arguments["<id>"]]
    else:
        search_filter += [("state", "=", "draft")]
    if not ids:
        print("# filtering: ", search_filter)
        ids = oerp.search('purchase.order', search_filter)
    # create output
    for order in oerp.browse('purchase.order', ids):
        print("# order {} for {}".format(order.name, order.partner_id.name))
        if order.state != "draft":
            print("#WARNING: this order is in state {}".format(order.state))
        for line in order.order_line:
            # try to fetch the product code from the product's supplier info entries
            product_code = False
            for supplierInfo in line.product_id.seller_ids:
                if supplierInfo.name == order.partner_id:  # this is the matching seller entry
                    product_code = supplierInfo.product_code
                    break
            if not product_code:
                print("# cannot find product code in supplier information for {}".format(line.name))
                product_code = line.name
            # print output
            print(get_formatstring(arguments["--format"], order.partner_id.name).format(
                qty=int_format(line.product_qty), code=product_code))
else:
    print("option not implemented")
