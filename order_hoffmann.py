# -*- coding: cp1252 -*-
from oerphelper import *
import argparse
import sys

try:
    import argcomplete
except ImportError:
    print >> sys.stderr, "Consider installing argcomplete"

# Hoffmann supplier ID
hoffmann_id = 47




def hoffmannCSV():
    """
    Converts an ERP purchase order to an Hoffmann comaptible .csv file
    """

    # parsing input arguments
    args = parse_args()
    
    # checking input
    orderName = args.orderName
    if orderName == '':
        print_error( 'No input.')
        exit(1)

    # set fileName [default = orderName]
    fileName = args.fileName
    if fileName == '':
        fileName = orderName

    # get purchase from input
    purchase = oerp.search('purchase.order',([('name', '=',orderName)]))

    # check if purchase existing
    if not purchase:
        print_error( 'No valid purchase order.')
        exit(1)

    # get purchase ID
    purchase_id = purchase[0]

    # check if purchase is by Hoffmann
    if oerp.browse('purchase.order',purchase_id).partner_id.id != hoffmann_id:
        print_error( orderName + ' is not a Hoffmann order.')
        exit(1)

    # initiating output variables 
    csv_output = ["Item No.;Size;Quantity"]
    products_fail = []
    products_warnings = []

    # get line IDs from purchase
    purchase_lines = oerp.read('purchase.order',purchase_id,["order_line"])['order_line']


    # check if purchase is not empty
    if not purchase_lines:
        print_error( orderName + ' has no items.')
        exit(1)

    # get list of purchase lines
    line_list = oerp.read('purchase.order.line',purchase_lines,['product_id','product_qty'])
    

    # iterate over purchase lines
    for line in line_list:
        # get product ID
        product_id = line['product_id'][0]
        # get relevant product fields
        product = oerp.read('product.product',product_id,['id','name','seller_ids','variants','variant_model_name','default_code','is_multi_variants'])
        # get seller IDs of the produce
        seller_ids = product['seller_ids']
        # check minimum one seller available
        if not seller_ids:
            products_fail.append('[' + str(product['id']) + '] ' + product['name'] + ' has no supplier and was ignored.')
            continue
        else:
            # check boolean if one seller is Hoffmann this will get true
            seller_is_hoffmann = False
            # get relevant supplier fields
            supplier = oerp.read('product.supplierinfo',seller_ids,['name','product_code'])
            # iterate over suppliers
            for seller in supplier:
                # check if Hoffmann is supplier
                if seller['name'][0] != hoffmann_id:
                    continue
                else:
                    # set check boolean true
                    seller_is_hoffmann = True
                    # get product_code
                    product_code = seller['product_code']
                    # check if product_code isnt empty
                    if product_code:
                        product_code = product_code.strip()
                        # check if pruduct is multi variant
                        if product['is_multi_variants']:
                            # get product_size out of multi variant
                            product_size = findVariant(product['variants'], product['variant_model_name']).strip()
                            product_code = product_code[:6].strip()
                        else:
                            # if not multivariant divide product_code in Hoffmann product_code and Hoffmann product_size
                            product_size = product_code[6:].strip()
                            product_code = product_code[:6].strip()

                        # check if product_size is empty, save warning for later output
                        if product_size == '':
                            products_warnings.append(('[' + str(product['default_code']) + '] ' + product['name'] + ' has no size, please check.'))
                        # write CSV line in Hoffmann style
                        csv_output.append(product_code + ";" + product_size + ";" + str(int(line['product_qty'])))
                    # save error if product_code is empty
                    else:
                        products_fail.append(('[' + str(product['default_code']) + '] ' + product['name'] + ' has no code and was ignored.'))
            # save error if Hoffmann was no supplier
            if seller_is_hoffmann is False:
                products_fail.append(('[' + str(product['default_code']) + '] ' + product['name'] + ' is not supplied by Hoffmann and was ignored.'))

    # write CSV file
    writeToFile(fileName, csv_output)

    # print conclusion of conversion
    conclusionPrinting(csv_output, products_fail, products_warnings, purchase_lines, fileName)




def writeToFile(fileName, csv_output):
    """
    Writing order to file
    """
    
    if len(csv_output) > 1:
        thefile = open( str(fileName) + '.csv','w+')
        for item in csv_output:
            thefile.write("%s\n" % item)
        thefile.close()




def conclusionPrinting(csv_output, products_fail, products_warnings, purchase_lines, fileName):
    """
    Printing conclusion of the conversion process
    """

    if len(csv_output) > 1:
        print (str(len(csv_output)-1) + ' out of ' + str(len(purchase_lines)) + ' have been sucessfull written to ' + fileName + '.csv')

    if products_fail:
        print_error (str(len(products_fail)) + ' errors occured.')
        for fail in products_fail:
            print_error(fail)

    if products_warnings:
        print_warning (str(len(products_warnings)) + ' warnings occured.')
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
        result = variants[position_left : (position_left + length)]
        
    return result




def parse_args():
    """
    Parses the command line arguments (e.g. -c --oerpcode) and returns them in an object
    """
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('orderName', metavar='n', type=str, default='', nargs='?',
                        help='Which Hoffmann order should be parsed to a CVS file?')
    parser.add_argument('fileName', metavar='n', type=str, default='', nargs='?',
                        help='Which name should ne the CVS file get?')
    
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
    hoffmannCSV()
