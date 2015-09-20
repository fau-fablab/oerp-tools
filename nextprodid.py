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

__authors__ = "Sebastian Endres <basti.endres@fablab.fau.de>," \
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


#TODO:
print(__authors__)



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


def main():
    args = parse_args()

    # validate
    if args.count < 1 or args.count > 10000:
        print_error("Count must be more than 0 and less than 10000.")
        exit(1)

    # get reserved ids from config file
    # Note: ids == product_ids == default_code
    config = read_config()

    # get non free ids from oerp and from config (reserved) both are invalid
    non_free_ids = oerp_get_prod_ids() + config["reserved"]

    # get enough free ids
    foundIds = []
    while len(foundIds) < args.count:
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
        codeId = -1337  # TODO
        first_id_of_sequence = foundIds[-args.count]  # the n-th last found id
        print_error("For new products only!")
        print_error("Be sure you have checked 'Don't Update Variant'!")
        print_error("Next unused id with {n} consecutive ids is '%04d'".format(n=args.count) % first_id_of_sequence)
        print_error("Enter the following code in the Code Generator")
        print("[_str(o.id%s)_]" % ("" if codeId is 0 else
                                   "-%d" % codeId if codeId > 0 else
                                   "+%d" % -codeId))

    sys.exit(0)
<<<<<<<merged HEAD von Basti
=======
def calculate_found_ids(quantity):
    """
    Returns requested number of foundIds
    """
    # get reserved ids from config file
    # Note: ids == product_ids == default_code
    config = read_config()

    # get all ids
    ids = oerp_get_prod_ids()

    i = 0
    foundIds = []
    while len(foundIds) < quantity:
        i += 1
        if i in config['reserved'] or i in ids:
            continue
        foundIds.append(i)
    return foundIds


def ids_in_Row(count, maxUsedId):
    """
    Finds the first id with N=count consecutive ones
    """

    # calculate maxUsedId unused default_codes
    foundIds = calculate_found_ids(maxUsedId)
    # check if foundIds is empty
    if not foundIds:
        print_error ("There are no more IDs available")
        sys.exit(1)
    # rowId is the starting ID with N consecutives
    rowId = 0
    # iterate over the findIds list
    for i in range(len(foundIds)-1):
        # check boolean if this number has N consecutives
        isRow = True
        # iterate over the N next numbers
        for j in range(count):
            # check if foundIds is out of range, then break
            if (i+j) > (len(foundIds)-1):
                isRow = False
                break
            # check if ID is not consecutive, then break
            if foundIds[i+j] != foundIds[i]+j:
                isRow = False
                break
        # check if this number has N consecutives, write to rowId and break
        if isRow:
            rowId = foundIds[i]
            return rowId
    return rowId


def main():
    args = parse_args()

    # if consecutive
    if args.consecutive:
        # larges default_codes usable in OERP
        maxUsedId = 9999
    else:
        # maximum unused IDs showing
        maxUsedId = 1000

    # validate
    if args.count < 1 or args.count > maxUsedId:
        print_error("Count must be more than 0 and less than " + str(maxUsedId) + ".")
        exit(1)

    # if not consecutive [default]
    if not args.consecutive:
        foundIds = calculate_found_ids(args.count)
        # print foundIds
        for i in foundIds:
            print("%04d" % i)
        sys.exit(0)
    else:
        rowId = ids_in_Row(args.count, maxUsedId)

        # check if one ID with N consective was found
        if rowId > 0:
            # check if OERPcode should not be printed [default]
            if not args.OERPcode:
                print ("%04d" % rowId)
            else:
                # get last used internal id in the erp
                last_id = max(oerp.search('product.product'))
                # calculate offset for OERPcode
                codeId = (last_id - rowId + 1)
                # print warning, how to use OERPcode
                print_error ("WARNING: For new products only!")
                print_error ("WARNING: Be sure you have checked \"Don't Update Variant\"!")
                # print next ID with N consecutives
                print ("Next unused id with " + str(args.consecutive) + " consecutive ids is %04d" % rowId)
                print ("Enter the following code in the Code Generator")
                # calculate Code Generator code
                if codeId > 0:
                    print ("[_str(o.id-" + str(codeId) + ")_]")
                elif codeId == 0:
                    print ("[_str(o.id)_]")
                else:
                    print ("[_str(o.id+" + str(-codeId) + ")_]")
        # if no ID was found
        else:
            print_error ("There are no " + str(args.count) + " consecutive IDs available")

>>>>>>> merge-nextprodid-nextnproid

if __name__ == "__main__":
    main()
