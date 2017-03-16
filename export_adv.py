#!/usr/bin/env python2.7
# -*- coding: cp1252 -*-
from oerphelper import *
from operator import itemgetter
import argparse
import sys

try:
    import argcomplete
except ImportError:
    print >> sys.stderr, "Consider installing argcomplete"


# supported suppliers
supplier_ids = {47: 'hoffmann', 116: 'textil'}

# initiating output variables
products_fail = []
products_warnings = []
csv_output = []


def convert_order():
    """
    Checks if purchase order exists, isn't emtpy and converts an ERP purchase order
    to an supplier comaptible file
    """
    # parsing input arguments
    args = parse_args()

    # checking input
    orderName = args.orderName
    if orderName == '':
        print_error('No input.')
        exit(1)

    # set fileName [default = orderName]
    fileName = args.fileName
    if fileName == None:
        fileName = orderName

    # get purchase from input
    purchase = oerp.search('purchase.order', ([('name', '=', orderName)]))

    # check if purchase existing
    if not purchase:
        print_error('No valid purchase order.')
        exit(1)

    # get purchase ID
    purchase_id = purchase[0]


    # check if purchase is supported
    supplier_id = oerp.read('purchase.order', purchase_id, ["partner_id"])['partner_id'][0]

    if supplier_id not in supplier_ids:
        print_error(orderName + ' is not by a supported supplier.')
        exit(1)
    
    # get line IDs from purchase
    purchase_lines = oerp.read('purchase.order', purchase_id, ["order_line"])['order_line']

    # check if purchase is not empty
    if not purchase_lines:
        print_error(orderName + ' has no items.')
        exit(1)

    # get list of purchase lines
    line_list = oerp.read('purchase.order.line',
                          purchase_lines,
                          ['product_id', 'product_qty'])

    supplier = supplier_ids[supplier_id]


    # iterate over purchase lines
    for line in line_list:
        # get product ID
        product_id = line['product_id'][0]
        # get relevant product fields
        product = oerp.read('product.product',
                            product_id,
                            ['id',
                             'name',
                             'seller_ids',
                             'variants',
                             'variant_model_name',
                             'default_code',
                             'is_multi_variants'])
        # get seller IDs of the product
        seller_ids = product['seller_ids']
        # check minimum one seller available
        if not seller_ids:
            products_fail.append('[' + str(product['id']) + '] ' + product['name'] + ' has no supplier and was ignored.')
            continue
        else:
            # check boolean if one seller is Hoffmann this will get true
            seller_is_true = False
            # get relevant supplier fields
            supplier = oerp.read('product.supplierinfo', seller_ids, ['name', 'product_code'])
            # iterate over suppliers
            for seller in supplier:
                # check if Hoffmann is supplier
                if seller['name'][0] != supplier_id:
                    continue
                else:
                    # set check boolean true
                    seller_is_true = True
                    # get product_code
                    product_code = seller['product_code']
                    # check if product_code isnt empty
                    if product_code:
                        product_code = product_code.strip()
                        
                        # Hoffmann
                        if supplier_id == 47:
                            # if CSV is empty, add header
                            initCSVoutput(["Item No.", "Size", "Quantity"])
                            product_size = hoffmannCSV(product_code, product, line)
                        # Textil
                        elif supplier_id == 116:
                            # if CSV is empty, add header
                            initCSVoutput(["Typ","Farbe","Größe","Anzahl"])
                            product_size = textilCSV(product_code, product, line)
                            
                        # check if product_size is empty, save warning for later output
                        if product_size == '':
                            products_warnings.append(('[' + str(product['default_code']) + '] ' + product['name'] + ' has no size, please check.'))
                    # save error if product_code is empty
                    else:
                        products_fail.append(('[' + str(product['default_code']) + '] ' + product['name'] + ' has no code and was ignored.'))
            # save error if Hoffmann was no supplier
            if seller_is_true is False:
                products_fail.append(('[' + str(product['default_code']) + '] ' + product['name'] + ' is not supplied by ' + supplier + ' and was ignored.'))


    # sort List if Textil-Großhandel
    if supplier_id == 116:
        # sort by T-Shirt size
        csv_output[1:] = sorted(csv_output[1:], key=lambda d: ["XS","S","M","L","XL","XXL"].index(d[2]))
        # sort by T-Shirt color
        csv_output[1:] = sorted(csv_output[1:], key=itemgetter(1))
        # sort by T-Shirt Type
        csv_output[1:] = sorted(csv_output[1:], key=itemgetter(0))
        
    
    # write CSV file
    writeToFile(fileName, csv_output)

    # print conclusion of conversion
    conclusionPrinting(csv_output, products_fail, products_warnings, purchase_lines, fileName)



def initCSVoutput(text):
    if len(csv_output) == 0:
        csv_output.append(text)

        

def hoffmannCSV(product_code, product, line):
    # check if pruduct is multi variant
    if product['is_multi_variants']:
        # get product_size out of multi variant
        product_size = findVariant(product['variants'], product['variant_model_name']).strip()
        product_code = product_code[:6].strip()
    else:
        # if not multivariant divide product_code in Hoffmann product_code and Hoffmann product_size
        product_size = product_code[6:].strip()
        product_code = product_code[:6].strip()
        
    # cutoff wrong product_size endings (e.g. diameter 1,0 => 1)
    if product_size[-2:]==',0':
        product_size = product_size[:-2]

    # write CSV line in Hoffmann style
    csv_output.append([product_code, product_size, str(int(line['product_qty']))])
    return product_size


def textilCSV(product_code, product, line):
    # check if pruduct is multi variant
    if product['is_multi_variants']:
        # get product_size out of multi variant
        product_size = findVariant(product['variants'], product['variant_model_name']).strip()
        product_size_1 = product_size[:product_size.find('-')].strip()
        product_size_2 = product_size[product_size.rfind('-')+1:].strip()
    else:
        # if not multivariant UNTESTED
        product_size_2 = product_code[product_code.rfind('-')+1:].strip()
        product_code_without_size_2 = product_code[:product_code.rfind('-')].strip()
        product_size_1 = product_code_without_size_2[product_code_without_size_2.rfind('-')+1:].strip()
        product_code_without_size = product_code_without_size_2[:product_code_without_size_2.rfind('-')].strip()
        product_code = product_code_without_size[product_code_without_size.rfind(' '):].strip()

    # write CSV line in Textil style
    csv_output.append([product_code, product_size_2, product_size_1, str(int(line['product_qty']))])
    return (product_size_2 + product_size_1)






def writeToFile(fileName, csv_output):
    """
    Writing order to file
    """

    if len(csv_output) > 1:
        thefile = open(str(fileName) + '.csv', 'w+')
        for item in csv_output:
            thefile.write("%s\n" % ';'.join(item))
        thefile.close()


def conclusionPrinting(csv_output, products_fail, products_warnings, purchase_lines, fileName):
    """
    Printing conclusion of the conversion process
    """

    if len(csv_output) > 1:
        print("'{nr}' out of '{cnt}' have been sucessfull written to '{fname}.csv'"
              .format(nr=len(csv_output)-1, cnt=len(purchase_lines), fname=fileName))

    if products_fail:
        print_error(str(len(products_fail)) + ' errors occured.')
        for fail in products_fail:
            print_error(fail)

    if products_warnings:
        print_warning(str(len(products_warnings)) + ' warnings occured.')
        for warning in products_warnings:
            print_warning(warning)

    exit(0)


def findVariant(variants, variant_model_name):
    """
    Extract the original varient value out of an multi variant product name
    """

    result = ''

    if variants is False:
        return result

    position_left = variant_model_name.find('[_')
    if position_left is -1:
        return result

    position_right = variant_model_name.find('_]') + 1
    if position_right is 0:
        return result

    function_length = position_right - position_left + 1
    length = - (len(variant_model_name) - len(variants) - function_length)

    if length > 0:
        result = variants[position_left: (position_left + length)]

    return result


def parse_args():
    """
    Parses the command line arguments (e.g. -c --oerpcode) and returns them in an object
    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('orderName', type=str, nargs='?',
                        help='Which order should be parsed to a CVS file?')
    parser.add_argument('fileName', type=str, nargs='?',
                        help='Which name should the CVS file get?')

    try:
        argcomplete.autocomplete(parser)
    except NameError:
        pass
    return parser.parse_args()


def print_error(message):
    """
    prints an error message to stderr
    """
    print >> sys.stderr, "[!] %s" % message


def print_warning(message):
    """
    prints an warning message to stdout
    """
    print >> sys.stdout, "[i] %s" % message

if __name__ == "__main__":
    convert_order()
