#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

"""
A small python script, to get the next available numeric product id
"""

import sys
import locale
import codecs
import argparse
from oerphelper import *
from ConfigParser import ConfigParser
try:
    import argcomplete
except ImportError:
    print >> sys.stderr, "Consider installing argcomplete"

__authors__ = "Sebastian Endres <basti.endres@fablab.fau.de>"
__license__ = "This program is free software: you can redistribute it and/or "
"modify it under the terms of the GNU General Public License as published by "
"the Free Software Foundation, either version 3 of the License, or (at your "
"option) any later version. "

"This program is distributed in the hope that it will be useful, but WITHOUT "
"ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS "
"FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. "

"You should have received a copy of the GNU General Public License along with "
"this program. If not, see <http://www.gnu.org/licenses/>."
__copyright__ = "Copyright (C) 2014 %s" % __authors__


# <editor-fold desc="argparse">
# </editor-fold>


def print_error(message):
    """
    prints an error message to stderr
    """
    print >> sys.stderr, "[!] %s" % message


def read_config():
    """
    reads the config.ini and returns a dict including the relevant values
    """
    base_path = os.path.dirname(__file__)
    configfile = os.path.abspath(os.path.join(base_path, "config.ini"))

    try:
        locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")
    except locale.Error:
        locale.setlocale(locale.LC_ALL, 'german_Germany')
    cfg = ConfigParser({})
    cfg.readfp(codecs.open(configfile, 'r', 'utf8'))
    res = cfg.get('nextprodid', 'reserved_ids').replace(' ', '').replace('[[', '').replace(']]', '')
    reserved = []
    if not res.replace('[', '').replace(']', '').replace(',', '') == '':
        res = res.split('],[')
        for i in res:
            reserved = reserved + range(int(i.split(',')[0]), int(i.split(',')[1]))
    return {'reserved': reserved}


def parse_args():
    """
    Parses the command line arguments (e.g. -c --oerpcode) and returns them in an object
    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('count', metavar='n', type=int, default=5, nargs='?',
                        help='how many available ids should be listed? [default 5]')
    try:
        argcomplete.autocomplete(parser)
    except NameError:
        pass
    return parser.parse_args()


def oerp_get_prod_ids():
    """
    queries all used 'default_code's from erp and returns them in a list
    """
    # get a list of dictionaries of products with their ids from oerp
    # ('active','>=',False) so that also deactivated products are found
    id_dict_list = oerp.read('product.product',
                             oerp.search('product.product',
                                         [('active', '>=', False)]),
                             ['default_code'])

    # extract default_code from dict
    ids = []
    for id_dict in id_dict_list:
        if str.isdigit(str(id_dict['default_code'])):
            ids.append(int(id_dict['default_code']))
    # ids = sorted(ids)
    return ids


def main():
    args = parse_args()

    # validate
    if args.count < 1 or args.count > 1000:
        print_error("Count must be more than 0 and less than 1000.")
        exit(1)

    # get reserved ids from config file
    config = read_config()

    ids = oerp_get_prod_ids()

    # get next unused default_code
    i = 0
    foundIds = []
    while len(foundIds) < args.count:
        i += 1
        if i in config['reserved'] or i in ids:
            continue
        foundIds.append(i)

    for i in foundIds:
        print("%04d" % i)
    sys.exit(0)

if __name__ == "__main__":
    main()
