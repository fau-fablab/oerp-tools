# OERP shortcut package

import oerplib
import locale
from ConfigParser import ConfigParser
import codecs
import os

locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

basepath = os.path.dirname(__file__)
configfile = os.path.abspath(os.path.join(basepath, "config.ini"))

cfg = ConfigParser({})
cfg.readfp(codecs.open(configfile, 'r', 'utf8'))

use_test = cfg.get('openerp', 'use_test').lower().strip() == 'true'
if use_test:
    print "[i] use testing database."
database = cfg.get('openerp', 'database_test') if use_test else cfg.get('openerp', 'database')
oerp = oerplib.OERP(server=cfg.get('openerp', 'server'), protocol='xmlrpc+ssl',
                    database=database, port=cfg.getint('openerp', 'port'),
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




# functions helping with the "newer style" .browse() API

def searchAndBrowse(db, filter):
    return oerp.browse(db, oerp.search(db, filter))
    
