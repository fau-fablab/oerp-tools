#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
# PYTHON_ARGCOMPLETE_OK

"""
A small python script, to get the next available N numeric product id, optional with searching for consecutive ones and print OERP multi variant code
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

__authors__ = "Sebastian Endres <basti.endres@fablab.fau.de>, Michael Jäger <michael.jaeger@fablab.fau.de>"
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

    parser.add_argument('count', metavar='N', type=int, default=5, nargs='?',
                        help='how many available/consecutive ids should be listed? [default 5]')
    parser.add_argument('consecutive', metavar='bool', type=bool, default=False, nargs='?',
                        help='search for consecutive IDs? [default FALSE]')
    parser.add_argument('OERPcode', metavar='bool', type=bool, default=False, nargs='?',
                        help='create code for multivariants products? [default FALSE]')
    

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


def calculate_found_ids(quantity):
    """
    Returns requested number of foundIds
    """
    # get reserved ids from config file
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


if __name__ == "__main__":
    main()
