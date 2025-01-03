#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# (C) Max Gaukler 2014
# unlimited usage allowed, see LICENSE file

# Dependencies


"""OpenERP Logo changer

Usage:
  oerpSetLogo.py read <database> <logoFile>
  oerpSetLogo.py write <database> <logoFile>

Options:
  -h --help     Show this screen.
  --version     Show version.

The logo is any standard image format
example: ./oerpSetLogo.py write production_test logo-testdatenbank.png

"""

from configparser import ConfigParser
import oerplib3 as oerplib
import locale
import codecs
from docopt import docopt
import base64

# dependencies:
# sudo pip install docopt

# switching to german:
locale.setlocale(locale.LC_ALL, "de_DE.UTF-8")

arguments = docopt(__doc__, version='blub')

cfg = ConfigParser({'foo': 'defaultvalue'})
cfg.readfp(codecs.open('config.ini', 'r', 'utf8'))

oerp = oerplib.OERP(server=cfg.get('openerp', 'server'), protocol='xmlrpc+ssl',
                    database=arguments['<database>'], port=cfg.getint('openerp', 'port'),
                    version=cfg.get('openerp', 'version'))
user = oerp.login(user=cfg.get('openerp', 'user'), passwd=cfg.get('openerp', 'password'))

c = oerp.search('res.company', [])
assert len(c) == 1, "need exactly 1 company"
companyId = c[0]

if arguments['read']:
    f = open(arguments['<logoFile>'], 'w')
    logo = oerp.read('res.company', companyId, ['logo'])['logo']
    logo = base64.b64decode(logo)
    f.write(logo)
    f.close()
elif arguments['write']:
    f = open(arguments['<logoFile>'], 'r')
    logo = f.read()
    f.close()
    company = oerp.browse('res.company', companyId)
    company.logo = base64.b64encode(logo)
    oerp.write_record(company)
else:
    raise Exception("unknown command")
