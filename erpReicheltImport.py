#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import locale
from ConfigParser import ConfigParser
import codecs
import oerplib
import sys
import pickle

#local imports
from sammelbestellung import pricefetcher, sammelbestellparser, sammelbestellung

locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

cfg = ConfigParser({})
cfg.readfp(codecs.open('config.ini', 'r', 'utf8'))

oerp = oerplib.OERP(server=cfg.get('openerp', 'server'), protocol='xmlrpc+ssl',
                    database=cfg.get('openerp', 'database'), port=cfg.getint('openerp', 'port'),
                    version='7.0')
user = oerp.login(user=cfg.get('openerp', 'user'), passwd=cfg.get('openerp', 'password'))

oerpContext={'lang': 'de_DE'}

class NotFound(Exception):
    pass
    
def getIds(db, filter):
    return oerp.search(db, filter, context=oerpContext)

def getId(db, filter):
    ids=getIds(db, filter)
    if not ids:
       raise NotFound("cannot find {} from search {}".format(db, str(filter)))
    assert len(ids)==1, "found more than one {} from search {}".format(db, str(filter))
    return ids[0]

#def getIds(db, filter):
#    return oerp.search(db, filter, context=oerpContext)

def read(db, id, fields=[]):
    readResult=oerp.read(db, [id], fields, context=oerpContext)
    if len(readResult)!=1:
        raise NotFound()
    return readResult[0]

def write(db, id, data):
    return oerp.write(db, [id], data, context=oerpContext)

def create(db, data):
    return oerp.create(db, data, context=oerpContext)

def readElements(db, filter, fields=[]):
    return oerp.read(db, getIds(db, filter), fields, context=oerpContext)

def readProperty(db, id, field, firstListItem=False):
    readResult=read(db, id, [field])
    property=readResult[field]
    if firstListItem:
        return property[0]
    else:
        return property

def categoryIdFromName(name):
    return getId('product.category', [('name', '=', name)])

def partnerIdFromName(name):
    return getId('res.partner', [('name', '=', name)])

def productIdFromName(name):
    return getId('product.product', [('name', '=', name), ('active', '=', True)])

def warehouseIdFromName(name):
    return getId('stock.warehouse', [('name', '=', name)])

def customerIdFromName(name):
    return getId('res.partner', [('name', '=', name), ('customer', '=', True)])

def productIdsFromSupplier(shopName, productCode):
    shop_id = getId('res.partner', [('name', '=', shopName)])
    try:
        supplierinfo_id=getId('product.supplierinfo',[('name','=',shop_id),('product_code','=',productCode)])
    except NotFound:
        return {'product':None, 'supplierinfo':None,  'shop': shop_id}
    product_id=readProperty('product.supplierinfo', supplierinfo_id, 'product_id', True)
    return {'product':product_id, 'supplierinfo':supplierinfo_id}


def fetchPrice(shopName, productCode, quantity=1):
    basket=pricefetcher.Basket()
    basket.add(pricefetcher.Part(shopName, productCode, quantity))
    basket.fetchPrices()
    return basket.parts()[0].price/quantity

def getSellingPrice(buyPrice, oldSellPrice):
    sellPrice=round(max([0.05, buyPrice*1.5]), 2)
    if oldSellPrice != None and sellPrice < 0.8*oldSellPrice - 0.02:
        print "WARNING: sell price should have dropped from {} to {} -- not changing.".format(oldSellPrice, sellPrice)
        sellPrice=oldSellPrice
    return sellPrice




def importOrUpdateProduct(shopName, productCode):
    buyPrice=fetchPrice(shopName, productCode)
    assert buyPrice != 0

    ids=productIdsFromSupplier(shopName,productCode)

    if ids['product']:
        # product exists, update price
        properties=read('product.product', ids['product'])
        
        purchase_uom_factor=1 # >1 if purchased in larger packages
        if properties['uom_id'] != properties['uom_po_id']:
            sale_uom=read('product.uom', properties['uom_id'][0])
            purchase_uom=read('product.uom', properties['uom_po_id'][0])
            assert sale_uom["category_id"]==purchase_uom["category_id"]
            # size of selected uom  (per reference uom)
            # example: uomGetFactor(pack_of_1000) = 1000, uomGetFactor(piece) = 1
            def uomGetFactor(d):
                return d["factor_inv"]
            purchase_uom_factor=uomGetFactor(purchase_uom)/uomGetFactor(sale_uom)
        
        sellPrice=getSellingPrice(buyPrice/purchase_uom_factor, properties['list_price'])
        write('product.product', ids['product'], {'standard_price': buyPrice/purchase_uom_factor, 'list_price': sellPrice})
        print u"updated {} {} price {} -> {}.  package size {}".format(shopName, productCode, properties['list_price'], sellPrice, purchase_uom_factor)
        
    else:
        print u"create {} {} price buy {}".format(shopName, productCode, buyPrice)
        sellPrice=getSellingPrice(buyPrice, None)
        properties={'standard_price': buyPrice, 'list_price': sellPrice,
                   'name': u'Import {} {}'.format(shopName, productCode), 
                   'categ_id': AUTOIMPORT_CATEGORY_ID
                   }
        ids['product']=create('product.product', properties)
        ids['supplierinfo']=create('product.supplierinfo', {'product_id':ids['product'], 'name':ids['shop'], 'product_code':productCode,  'min_qty':1})

    # update or create supplicer pricelist
    supplierinfo=read('product.supplierinfo', ids['supplierinfo'], ['pricelist_ids'])
    if len(supplierinfo['pricelist_ids']) > 1:
        raise Exception("Staffelpreise unsupported")
    elif len(supplierinfo['pricelist_ids']) == 1:
        pricelistId=supplierinfo['pricelist_ids'][0]
        write('pricelist.partnerinfo', pricelistId, {'min_quantity':1, 'price':buyPrice})
    else:
        # length=0 
        create('pricelist.partnerinfo', {'suppinfo_id':ids['supplierinfo'],'min_quantity':1, 'price':buyPrice})


# importOrUpdateProduct('reichelt.de', 'NE 556 DIL')



# create purchase order:

def getDefault(db, fields):
    return oerp.execute(db, 'default_get', fields) # TODO does not send the id of the currently edited record like the web-GUI does. still works.

# call onchange handler to fetch related default values
# usage example:
#   data=callOnchangeHandler(...)
#   data.update(callOnchangeHandler(db, field2, value2))
#   data["foo"]="bar"
#   data.update(....)
#   oerp.create(db, data)
def callOnchangeHandler(db, field, value):
    reply=oerp.execute(db, 'onchange_'+field, [], value) # TODO does not send the id of the currently edited record like the web-GUI does. still works.
    assert (not reply.has_key('warning') or not reply["warning"]), "failed calling onchange-handler,  reply:"+str(reply)
    update=dict(reply["value"])
    update[field]=value
    return update

print "TODO: Kommentar am Zeilenende bei export, versandkosten nicht mit --cache funktionierend, Funktion um Mails zu schicken und VK AUftrag abzuschließen, VK Auftrag vorher noch auf Entwurf lassen damit einfacher löschbar, exportNativeBasket nutzen"

AUTOIMPORT_CATEGORY_ID=categoryIdFromName('automatisch importiert')
SHIPPINGCOST_PRODUCT_ID=productIdFromName("Versandkosten")

if sys.argv[1]=="export":
    # export openERP -> csv
    currentShop=sys.argv[2]
    shop_id=partnerIdFromName(currentShop)
    
    filter=[("state", "=", "draft"), ("partner_id", "=", shop_id)]
    if len(sys.argv) > 3:
        filter=[("name", "=", sys.argv[3])]
    for orderId in getIds('purchase.order', filter):
        print u"# order {}".format(orderId)
        for orderline in readElements('purchase.order.line', [('order_id', '=', orderId)], []):
            #product=read('product.product', orderline["product_id"])
            try:
                supplierinfo_id=readProperty('product.product',orderline["product_id"][0], 'seller_ids', firstListItem=True)
                supplierinfo=read('product.supplierinfo', supplierinfo_id)
                                
                # fix string output: print ints as 123 and not 123.0
                if orderline["product_qty"] == int(orderline["product_qty"]):
                    orderline["product_qty"] = int(orderline["product_qty"])
                print u"{1};{0}".format(orderline["product_qty"],supplierinfo["product_code"]) # ,orderline["product_uom"][1])
            except NotFound:
                print u"# cannot find article: {}".format(orderline["product_id"][1])
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
