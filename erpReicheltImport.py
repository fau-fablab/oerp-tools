#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import locale
from ConfigParser import ConfigParser
import codecs
import oerplib

#local imports
from sammelbestellung import pricefetcher

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

def getId(db, filter):
    ids=oerp.search(db, filter, context=oerpContext)
    if not ids:
       raise NotFound("cannot find {} from search {}".format(db, str(filter)))
    assert len(ids)==1, "found more than one {} from search {}".format(db, str(filter))
    return ids[0]

def read(db, id, fields=[]):
    readResult=oerp.read(db, [id], fields, context=oerpContext)
    if len(readResult)!=1:
        raise NotFound()
    return readResult[0]

def write(db, id, data):
    return oerp.write(db, [id], data, context=oerpContext)

def create(db, data):
    return oerp.create(db, data, context=oerpContext)

def readProperty(db, id, field, firstListItem=False):
    readResult=read(db, id, [field])
    property=readResult[field]
    if firstListItem:
        return property[0]
    else:
        return property

def categoryIdFromName(name):
    return getId('product.category', [('name', '=', name)])

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
        sellPrice=properties['list_price']
    return sellPrice




def importOrUpdateProduct(shopName, productCode):
    buyPrice=fetchPrice(shopName, productCode)
    assert buyPrice != 0

    ids=productIdsFromSupplier(shopName,productCode)

    if ids['product']:
        # product exists, update price
        properties=read('product.product', ids['product'])
        assert properties['uom_id'] == properties['uom_po_id'],  "unsupported: product with UOMs   sell != buy"
        
        sellPrice=getSellingPrice(buyPrice, properties['list_price'])
        write('product.product', ids['product'], {'standard_price': buyPrice, 'list_price': sellPrice})
        print "updated {} {} price {} -> {}".format(shopName, productCode, properties['list_price'], sellPrice)
        
    else:
        sellPrice=getSellingPrice(buyPrice, None)
        properties={'standard_price': buyPrice, 'list_price': sellPrice,
                   'name': 'Import {} {}'.format(shopName, productCode), 
                   'categ_id': categoryIdFromName('automatisch importiert') # TODO HARDCODED!
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


importOrUpdateProduct('reichelt.de', 'NE 556 DIL')
