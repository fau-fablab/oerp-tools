#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK
#
# Copyright (C) 2014  Sebastian Endres <basti.endres@fablab.fau.de>
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

from oerphelper import *
import sys
from ConfigParser import ConfigParser
import locale
import codecs
import argparse
import argcomplete


# <editor-fold desc="argparse">
parser = argparse.ArgumentParser(description='A small python script, to get the next available numeric product id')

parser.add_argument('consecutive', metavar='n', type=int, help='how many consecutive ids should be listed? [default 5]',
                    default=5, nargs='?')
parser.add_argument('OERPcode', metavar='n', type=bool, help='create code for multivariants products? [default FALSE]',
                    default=False, nargs='?')

argcomplete.autocomplete(parser)

args = parser.parse_args()

# validate
maxUsedId = 9999
if args.consecutive <= 1 or args.consecutive > maxUsedId:
    print '[!] consecutive must be more than 1 or less than 10000.'
    exit(1)
# </editor-fold>

base_path = os.path.dirname(__file__)
configfile = os.path.abspath(os.path.join(base_path, "config.ini"))

# get reserved ids from config file
locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
cfg = ConfigParser({})
cfg.readfp(codecs.open(configfile, 'r', 'utf8'))
res = cfg.get('nextprodid', 'reserved_ids').replace(' ', '').replace('[[', '').replace(']]', '')
reserved = []
if not res.replace('[', '').replace(']', '').replace(',', '') == '':
    res = res.split('],[')
    for i in res:
        reserved = reserved + range(int(i.split(',')[0]), int(i.split(',')[1]))

# get ids dictionary from oerp
# ('active','>=',False) so that also deactivated products are found
id_dict_list = oerp.read('product.product', oerp.search('product.product', [('active', '>=', False)]), ['default_code'])


# get last used id
last_id = max(oerp.search('product.product'))


# extract default_code from dict
ids = []
for id_dict in id_dict_list:
    if str.isdigit(str(id_dict['default_code'])) and not int(id_dict['default_code'] in reserved):
        ids.append(int(id_dict['default_code']))

# ids = sorted(ids)

# get next unused args.consecutive IDs default_code
i = 0
foundIds = []

while i < maxUsedId:
    i += 1
    if i in reserved or i in ids:
        continue
    foundIds.append(i)

rowId = 0
for i in range(len(foundIds)-1):
    isRow = True
    for j in range(args.consecutive):
        if (i+j) > (len(foundIds)-1):
            isRow = False
            break
        if foundIds[i+j] != foundIds[i]+j:
            isRow = False
            break
    if isRow:
        rowId = foundIds[i]
        break

if rowId > 0:
    if args.OERPcode:
        codeId = (last_id - rowId + 1)
        print ("WARNING: For new products only!")
        print ("WARNING: Be sure you have checked \"Don't Update Variant\"!")
        print ("Next unused id with " + str(args.consecutive) + " consecutive ids is %04d" % rowId)
        print ("Enter the following code in the Code Generator")
        if codeId > 0:
            print ("[_str(o.id-" + str(codeId) + ")_]")
        elif codeId == 0:
            print ("[_str(o.id)_]")
        else:
            print ("[_str(o.id+" + str(-codeId) + ")_]")
    else:
        print ("%04d" % rowId)
else:
    print ("There are no " + str(args.consecutive) + ' consecutive IDs available')

sys.exit(0)
