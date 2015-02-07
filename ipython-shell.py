#!/usr/bin/ipython -i
# -*- coding: utf-8 -*-
print ""
print "connecting to OERP"
from oerphelper import *
import datetime # for editing dates
print "now use oerp.browse, read, write, ... or the helper functions read() etc"
print """quick intro:
a=oerp.browse('product.product',142);
use autoexpansion:
a.<Tab>
change something:
a.name="Quarz 16 MHz SMD HC49-SMD"
write to DB:
oerp.write_record(a)

http://oerplib.readthedocs.org/
http://oerplib.readthedocs.org/en/latest/tutorials.html

Obacht, mit der API kann man viele blödsinnige Dinge machen, die das Webinterface verbietet!
"""

