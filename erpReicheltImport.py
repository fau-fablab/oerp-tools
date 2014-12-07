#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

# TODO: this is ugly... make it a nice package
from oerphelper import *
from oerphelper_pricefetcher import *

import sys
import pickle

# importOrUpdateProduct('reichelt.de', 'NE 556 DIL')

print "TODO: Kommentar am Zeilenende bei export, versandkosten nicht mit --cache funktionierend, Funktion um Mails zu schicken und VK AUftrag abzuschließen, VK Auftrag vorher noch auf Entwurf lassen damit einfacher löschbar, exportNativeBasket nutzen"

AUTOIMPORT_CATEGORY_ID=categoryIdFromName('automatisch importiert')
SHIPPINGCOST_PRODUCT_ID=productIdFromName("Versandkosten")



if sys.argv[1]=="export":
    print "sorry, this feature moved to export.py"
            
elif sys.argv[1]=="import":
    # import sammelbestellung-basket -> ERP
    if "--cached" in sys.argv:
        [buyers, origin, settings, totalBasket, totalSums]=pickle.load(open(sys.argv[2]+".cache", "rb"))
    else:
        [buyers, origin, settings, totalBasket, totalSums]=sammelbestellung.parseAndFetch(sys.argv[2])
        pickle.dump([buyers, origin, settings, totalBasket, totalSums], open(sys.argv[2]+".cache", "wb"))
    
    if (not "--cached" in sys.argv) or ("--force-import" in sys.argv):
        print "Importiere / aktualisiere Produkte"
        for part in totalBasket.parts():
             importOrUpdateProduct(part.shop, part.partNr)

    # check that all buyers exist
    for buyer in buyers:
        if buyer.name=="FabLab": # HARDCODED
            continue
        customerIdFromName(buyer.name)
    
    print u"Erzeuge Einkaufsaufträge:"

    for currentShop in totalBasket.shops():
        order_data=getDefault('purchase.order', ["origin","message_follower_ids","order_line","company_id","currency_id","date_order","location_id","message_ids","invoiced","dest_address_id","fiscal_position","amount_untaxed","partner_id","journal_id","amount_tax","state","pricelist_id","warehouse_id","payment_term_id","partner_ref","date_approve","amount_total","name","notes","invoice_method","shipped","validator","minimum_planned_date"])
        partner_id=partnerIdFromName(currentShop)
        order_data.update(callOnchangeHandler('purchase.order', 'partner_id', partner_id))
        order_data.update(callOnchangeHandler('purchase.order', 'warehouse_id',  warehouseIdFromName("FAU FabLab")))
        order_data["minimum_planned_date"]=False
        order_id = oerp.create('purchase.order', order_data)

        #        else:
        #        order_id = self.orders[self.current_order]

        # get pricelist id
        order_data = oerp.read('purchase.order', order_id, [])
        print u"Erzeuge Einkaufsauftrag {} für {}".format(order_data["name"], currentShop)
        #print order_data

        def addPartToPurchaseOrder(prod_id, count, price, purchaseOrderData):
            # TODO order_id is implicitly passed, change this
            # Calculate price
            # from view XML: onchange_product_id(parent.pricelist_id,product_id,product_qty,product_uom,parent.partner_id,parent.date_order,parent.fiscal_position,date_planned,name,price_unit,context)
            order_line_data = oerp.execute(
                # onchange_product_id(                      currentRecord,
                'purchase.order.line', 'onchange_product_id', [],
                #  uid, ids, pricelist_id, product_id, qty, uom_id, partner_id, [...])
                False, prod_id, count, False, purchaseOrderData["partner_id"][0], purchaseOrderData["date_order"], purchaseOrderData["fiscal_position"], False, False, False)
            if order_line_data['warning']:
                raise Exception(u"warning:"+unicode(order_line_data))
            order_line_data=order_line_data['value']
            order_line_data.update({'order_id': order_id, 'product_id': prod_id,
                                    'product_qty': count, 'price_unit':price})
            order_line_id = oerp.create('purchase.order.line', order_line_data)

        for part in totalBasket.parts():
            if part.shop != currentShop:
                continue
            prod_id=productIdsFromSupplier(part.shop, part.partNr)['product']
            addPartToPurchaseOrder(prod_id, part.count, part.price, order_data)
        addPartToPurchaseOrder(SHIPPINGCOST_PRODUCT_ID, pricefetcher.shopByName(currentShop).shipping, 1.00, order_data) # HARDCODED

    print "Erzeuge Verkaufsaufträge:"

    def addPartToSaleOrder(prod_id, count, price):
        # Calculate price
        order_line_data = oerp.execute(
            'sale.order.line', 'product_id_change', [],
            order_data['pricelist_id'][0], prod_id, count,
            # UOM  qty_uos UOS    Name   partner_id
            False, 0,      False, False, partner_id)['value']
        order_line_data.update({'order_id': order_id, 'product_id': prod_id,
                                'product_uom_qty': count, 'price_unit':price})
        order_line_id = oerp.create('sale.order.line', order_line_data)


    orderIds=[]


    # create orders per buyer

    for buyer in buyers:
        if buyer.name=="FabLab": # HARDCODED
            print "skipping FabLab, it is not a customer"
            continue
        partner_id=customerIdFromName(buyer.name)
        
        # Select or create order
        # Create new order
        order_data = oerp.execute('sale.order', 'onchange_partner_id', [], partner_id)
        assert not order_data['warning'], "failed getting default values for sale.order"
        order_data = order_data['value']
        order_data.update({'partner_id': partner_id})
        order_id = oerp.create('sale.order', order_data)
        orderIds.append(order_id)
    #        else:
    #        order_id = self.orders[self.current_order]

        order_data = oerp.read('sale.order', order_id, [])
        print u"Erzeuge Verkaufsauftrag {} für Kunde {}".format(order_data["name"], buyer.name)

        for part in buyer.basket.parts():
            prod_id=productIdsFromSupplier(part.shop, part.partNr)['product']
            addPartToSaleOrder(prod_id, part.count, part.price)
        addPartToSaleOrder(SHIPPINGCOST_PRODUCT_ID, buyer.totalShipping, 1.00) # HARDCODED

    print "Bestätige Verkaufsaufträge."
    for order_id in orderIds:
        oerp.exec_workflow('sale.order', 'order_confirm', order_id)

    print "EK-Auftrag bitte manuell bestätigen sobald Ware bestellt."
else:
    print "usage: reicheltimport.py import / export"
