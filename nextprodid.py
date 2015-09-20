#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

"""
A small python script, to get the next available n numeric product id,
optional with searching for consecutive ones and print OERP multi variant code
"""

import sys
import locale
import codecs
import json
import argparse
from oerphelper import *
from ConfigParser import ConfigParser
try:
    import argcomplete
except ImportError:
    print >> sys.stderr, "Consider installing argcomplete"

__authors__ = "Sebastian Endres <basti.endres@fablab.fau.de>, " \
              "Michael Jäger <michael.jaeger@fablab.fau.de>"
__license__ = "This program is free software: you can redistribute it and/or "
"modify it under the terms of the GNU General Public License as published by "
"the Free Software Foundation, either version 3 of the License, or (at your "
"option) any later version. "

"This program is distributed in the hope that it will be useful, but WITHOUT "
"ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS "
"FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. "

"You should have received a copy of the GNU General Public License along with "
"this program. If not, see <http://www.gnu.org/licenses/>."
__copyright__ = "Copyright (C) 2015 %s" % __authors__


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
    # parse reserved ids
    res = cfg.get('nextprodid', 'reserved_ids').strip()
    res_json = json.loads(res if res != "" else "[]")
    reserved = []
    for r in res_json:
        reserved += [int(r)] if not isinstance(r, list) else range(int(r[0]), int(r[-1])+1)
    return {'reserved': reserved}


def parse_args():
    """
    Parses the command line arguments (e.g. -c --oerpcode) and returns them in an object
    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('count', metavar='n', type=int, default=5, nargs='?',
                        help='how many available ids should be listed? [default 5]')
    parser.add_argument('-c', '--consecutive', dest='consecutive',
                        default=False, action='store_true',
                        help="should the ids be consecutive? [default FALSE]")
    parser.add_argument('-o', '--oerpcode', dest='oerp_code',
                        default=False, action='store_true',
                        help="create code for multivariants products? (implicates --consecutive) [default FALSE]")

    try:
        argcomplete.autocomplete(parser)
    except NameError:
        pass

    # oerp_code only works with consecutive ids...
    args = parser.parse_args()
    if args.oerp_code:
        args.consecutive = True
    return args


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


def oerp_get_max_internal_id():
    """
    queries the maximum used internal id
    :returns: the maximum used internal_id
    """
    return max(oerp.search('product.product'))


def get_free_id(non_free_ids, start_id=0):
    """
    returns one id, which is not in non_free_ids
    :param non_free_ids: a list of invalid ids (reserved or occupied)
    :param start_id: the id to start with (first run 0; if 2 was found before -> 3)
    """
    while start_id < 10000:
        # while the id is a 4 digit number
        if start_id not in non_free_ids:
            return start_id
        start_id += 1
    print_error("There is no id left")
    exit(1337)


def signum(number): return '+' if number > 0 else '-' if number < 0 else ''


def strip0(number): return '' if number == 0 else '%d' % number


def main():
    args = parse_args()

    # validate
    if args.count < 1 or args.count > 9999:
        print_error("Count must be more than 0 and less than 10000.")
        exit(1)

    # get reserved ids from config file
    # Note: ids == product_ids == default_code != internal_id
    config = read_config()

    # get non free ids from oerp and from config (reserved) both are invalid
    non_free_ids = oerp_get_prod_ids() + config["reserved"]

    # get enough free ids
    foundIds = []
    while len(foundIds) < args.count:
        # receive the next free id and start with the last found id + 1
        # or with 0 when list is empty
        free_id = get_free_id(non_free_ids, foundIds[-1]+1 if len(foundIds) else 0)
        if not args.consecutive or not len(foundIds) or free_id == foundIds[-1] + 1:
            # we don't want consecutive or we want cons. and the found number
            # is 1 greater than the number before, or it is the first number
            foundIds.append(free_id)
        else:
            # we want consecutive but this wasn't consecutive -> maybe free_id
            # is the first free id of the sequence
            foundIds = [free_id]

    if not args.oerp_code:
        # list ids
        for i in foundIds:
            print("%04d" % i)
    else:
        # create special OERP code
        # foundIds[0] is the first found id in sequence
        # calculate the offset between OERPs internal_id and our default_code
        offset = foundIds[0] - oerp_get_max_internal_id() - 1
        print_error("For new products only!")
        print_error("Be sure you have checked 'Don't Update Variant'!")
        print_error("Next unused id with {n} consecutive ids is '%04d'".
                    format(n=args.count) % foundIds[0])
        print_error("Enter the following code in the Code Generator")
        print("[_str(o.id{s}{n})_]".format(s=signum(offset),
                                           n=strip0(abs(offset))))

    sys.exit(0)

if __name__ == "__main__":
    main()
