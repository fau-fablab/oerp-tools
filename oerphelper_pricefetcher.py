#!/usr/bin/python2.7
# OERP-pricefetcher-connector
from sammelbestellung import pricefetcher, sammelbestellung


def fetchPrice(shopName, productCode, quantity=1):
    basket = pricefetcher.Basket()
    basket.add(pricefetcher.Part(shopName, productCode, quantity))
    basket.fetchPrices()
    return basket.parts()[0].price / quantity


def getSellingPrice(buyPrice, oldSellPrice):
    sellPrice = round(max([0.05, buyPrice * 1.5]), 2)
    if oldSellPrice != None and sellPrice < 0.8 * oldSellPrice - 0.02:
        print "WARNING: sell price should have dropped from {} to {} -- not changing.".format(oldSellPrice, sellPrice)
        sellPrice = oldSellPrice
    return sellPrice


def importOrUpdateProduct(shopName, productCode):
    buyPrice = fetchPrice(shopName, productCode)
    assert buyPrice != 0

    ids = productIdsFromSupplier(shopName, productCode)

    if ids['product']:
        # product exists, update price
        properties = read('product.product', ids['product'])

        purchase_uom_factor = 1  # >1 if purchased in larger packages
        if properties['uom_id'] != properties['uom_po_id']:
            sale_uom = read('product.uom', properties['uom_id'][0])
            purchase_uom = read('product.uom', properties['uom_po_id'][0])
            assert sale_uom["category_id"] == purchase_uom["category_id"]
            # size of selected uom  (per reference uom)
            # example: uomGetFactor(pack_of_1000) = 1000, uomGetFactor(piece) = 1

            def uomGetFactor(d):
                return d["factor_inv"]

            purchase_uom_factor = uomGetFactor(purchase_uom) / uomGetFactor(sale_uom)

        sellPrice = getSellingPrice(buyPrice / purchase_uom_factor, properties['list_price'])
        write('product.product', ids['product'],
              {'standard_price': buyPrice / purchase_uom_factor, 'list_price': sellPrice})
        print u"updated {} {} price {} -> {}.  package size {}".format(shopName, productCode, properties['list_price'],
                                                                       sellPrice, purchase_uom_factor)

    else:
        print u"create {} {} price buy {}".format(shopName, productCode, buyPrice)
        sellPrice = getSellingPrice(buyPrice, None)
        properties = {
            'standard_price': buyPrice, 'list_price': sellPrice,
            'name': u'Import {} {}'.format(shopName, productCode),
            'categ_id': AUTOIMPORT_CATEGORY_ID
        }
        ids['product'] = create('product.product', properties)
        ids['supplierinfo'] = create('product.supplierinfo',
                                     {'product_id': ids['product'], 'name': ids['shop'], 'product_code': productCode,
                                      'min_qty': 1})

    # update or create supplicer pricelist
    supplier_info = read('product.supplierinfo', ids['supplierinfo'], ['pricelist_ids'])
    if len(supplier_info['pricelist_ids']) > 1:
        raise Exception("Staffelpreise unsupported")
    elif len(supplier_info['pricelist_ids']) == 1:
        pricelist_id = supplier_info['pricelist_ids'][0]
        write('pricelist.partnerinfo', pricelist_id, {'min_quantity': 1, 'price': buyPrice})
    else:
        # length=0 
        create('pricelist.partnerinfo', {'suppinfo_id': ids['supplierinfo'], 'min_quantity': 1, 'price': buyPrice})

