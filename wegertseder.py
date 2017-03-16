#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
Füge Wegertseder als Lieferant für alle Schrauben und so hinzu.

Daten muss man von der Website aus den Tabellen kopieren und in ein CSV füttern.

Folgende Spalten müssen im CSV enthalten sein:
artikel_nummer	groesse	anzahl_klein	preis_klein	anzahl_mittel	preis_mittel	anzahl_gross	preis_gross	artikel_name	artikel_typ

Beispiel:
2600-208	M 3 x 5			500	22.91	2500	100.56	DIN 7991 Senkschrauben mit Innensechskant	8.8 - verzinkt
2600-798	M 3 x 6	50	2.62	500	10.71	5000	91.04	DIN 7991 Senkschrauben mit Innensechskant	8.8 - verzinkt
2600-800	M 3 x 8	100	3.27	500	7.26	5000	59.5	DIN 7991 Senkschrauben mit Innensechskant	8.8 - verzinkt
"""

from oerphelper import *
from csv import DictReader
    
CSV_FILE_NAME = './wegertseder.csv'
OERP_PRODUCT_NAMES = {
    'DIN 7991': u'Senkschraube\xa0DIN\xa07991\xa0‐ {groesse}\xa0‐\xa08.8',
    'DIN 933': u'Sechskantschraube\xa0DIN\xa0933\xa0‐ {groesse}\xa0‐\xa08.8',
    'DIN 912': u'Zylinderschraube\xa0DIN\xa0912 ‐ {groesse}\xa0‐\xa08.8',
}

Wegertseder_id = 202

def updatePriceWegertseder():
    NewLabelsToPrint = []
    with open(CSV_FILE_NAME, 'r') as csvfile:
        reader = DictReader(csvfile, delimiter=';')
        for row in reader:
            name = ''
            #print(row)
            for key, value in OERP_PRODUCT_NAMES.items():
                if key in row['artikel_name']:
                    name = value
                    break
    
            if not name:
                print('Ignoring row', row)
                continue
    
            value_groesse = row['groesse'].replace(' ', '', 1).replace(' ', u'\xa0').strip()
            name = name.format(groesse = value_groesse)
            #print('groesse: %s' % value_groesse)
            #print('name: %s' % name)
    
            prod_id = oerp.search('product.product', [('name','like', name)])
            if (prod_id):
                print('name: %s (ID: %i)' % (name, prod_id[0]))
                if (len(prod_id) > 1):
                    print('Error: More then one product found!')
                    break
                else:
                    product = oerp.read('product.product',
                                        prod_id[0],
                                        ['product_tmpl_id',
                                         'seller_ids'])
                    # get seller IDs of the product
                    seller_ids = product['seller_ids']
                    product_tmpl_id = product['product_tmpl_id'][0]
                    # check minimum one seller available
                    if seller_ids:
                            # get relevant supplier fields
                            supplier = oerp.read('product.supplierinfo', seller_ids, ['name'])
                            # iterate over suppliers
                            for seller in supplier:
                                if seller['name'][0] == Wegertseder_id:
                                    product = oerp.browse('product.product',prod_id[0])
                                    if (row['preis_mittel']):
                                        updateNeeded = False
                                        newBuyPrice = round(float(row['preis_mittel']) / int(row['anzahl_mittel']),4)
                                        if product.standard_price == newBuyPrice:
                                            print('Purchasing price doesn\'t need to be updated')
                                        else:
                                            product.standard_price = newBuyPrice
                                            updateNeeded = True
                                            print('Purchasing price successfully updated')
                                        if product.list_price < product.standard_price:
                                            oldPrice = product.list_price
                                            product.list_price = max(round(product.standard_price * 1.5, 2), 0.05)
                                            print('Sales price has to be updated from %.2f € to %.2f €' % (oldPrice, product.list_price))
                                            NewLabelsToPrint.append(prod_id[0])
                                            updateNeeded = True
                                        if updateNeeded:
                                            oerp.write_record(product)
                return #remove before flight
                                    



def addWegertseder():
    with open(CSV_FILE_NAME, 'r') as csvfile:
        reader = DictReader(csvfile, delimiter=';')
        for row in reader:
            name = ''
            #print(row)
            for key, value in OERP_PRODUCT_NAMES.items():
                if key in row['artikel_name']:
                    name = value
                    break
    
            if not name:
                print('Ignoring row', row)
                continue
    
            value_groesse = row['groesse'].replace(' ', '', 1).replace(' ', u'\xa0').strip()
            name = name.format(groesse = value_groesse)
            #print('groesse: %s' % value_groesse)
            #print('name: %s' % name)
    
            prod_id = oerp.search('product.product', [('name','like', name)])
            if (prod_id):
                print('name: %s (ID: %i)' % (name, prod_id[0]))
                if (len(prod_id) > 1):
                    print('Error: More then one product found!')
                    break
                else:
                    product = oerp.read('product.product',
                                        prod_id[0],
                                        ['product_tmpl_id',
                                         'seller_ids'])
                    # get seller IDs of the product
                    seller_ids = product['seller_ids']
                    product_tmpl_id = product['product_tmpl_id'][0]
                    addSupplier = True
                    # check minimum one seller available
                    if seller_ids:
                            # get relevant supplier fields
                            supplier = oerp.read('product.supplierinfo', seller_ids, ['name'])
                            # iterate over suppliers
                            for seller in supplier:
                                if seller['name'][0] == Wegertseder_id:
                                    addSupplier = False
                                    print('Supplier for this product already exists!')
                                else:
                                    otherseller = oerp.browse('product.supplierinfo', seller['id'])
                                    otherseller.sequence = 2
                                    oerp.write_record(otherseller)
                                    
                    if addSupplier:
                        supplier_product_name = row['artikel_name'] + ' ' + row['artikel_typ']
                        quantity = []
                        if (row["anzahl_klein"]):
                            quantity.append({'min_quantity': int(row['anzahl_klein']),
                                             'price': float(row['preis_klein']) / int(row['anzahl_klein'])})
                        if (row["anzahl_mittel"]):
                            quantity.append({'min_quantity': int(row['anzahl_mittel']),
                                             'price': float(row['preis_mittel']) / int(row['anzahl_mittel'])})
                        if (row["anzahl_gross"]):
                            quantity.append({'min_quantity': int(row['anzahl_gross']),
                                             'price': float(row['preis_gross']) / int(row['anzahl_gross'])})
                        createSupplierinfo(product_tmpl_id, 
                                           Wegertseder_id, 
                                           supplier_product_name, 
                                           row['artikel_nummer'],
                                           row["anzahl_mittel"],
                                           quantity)
                        print('Supplier sucessfully added!')    
                return #remove before flight



def createSupplierinfo(product_tmpl_id, 
                       supplier_id, 
                       supplier_product_name, 
                       supplier_product_code, 
                       min_qty,
                       quatity_prices = [], 
                       delay = 7):
    data = {'delay': delay,
            'name': supplier_id,
            'product_code': supplier_product_code,
            'product_name': supplier_product_name,
            'product_id': product_tmpl_id,
            'min_qty': min_qty}
    new_seller_info_id = oerp.create('product.supplierinfo', data)
    
    for pricelists in quatity_prices:
        price_data = {'suppinfo_id': new_seller_info_id,
                      'min_quantity': pricelists['min_quantity'],
                      'price': pricelists['price']}
        oerp.create('pricelist.partnerinfo',price_data )
    return