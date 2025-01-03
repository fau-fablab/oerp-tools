oerp-tools
==========

Hacky commandlinetools and a small webinterface for things that should rather be [OERP](https://github.com/odoo/odoo) plugins.

##Content

 - `export.py`: Exports orders, lists quantity and product ids from orders in oerp.
 - `nextprodid.py`: A small python script, to get the next available numeric product id.
 - `ipython-shell.py`: A ipython shell for the [oerp library](https://pypi.python.org/pypi/OERPLib/)
 - `oerphelper.py`: A helper library for python scripts.
 - `set-logo.py`: get/set the company logo (`set-logo.py write production_test example-data/logo-testdatenbank.png`)
 - `erpReicheltImport.py`: Imports Reichelt-shoppingcarts into the ERP automagically.

##Dependencies
* python3
* oerplib3 (included locally)

##Usage
```bash
  git clone --recursive  https://github.com/fau-fablab/oerp-tools
  cd oerp-tools/src
  cp config.ini.example config.ini
  # config.ini anpassen
  # Userlogin dafür verwenden
  # database Namen anpassen an Datenbanknamen (z.B. production, testing)
  # und bei use_test True od. False eintragen (development oder production)
```

### Docker
```
docker-compose build
docker-compose run oerptools bash
# jetzt ausführen z.B.
./nextprodid.py
```

### - [`export.py`](export.py)
Angebote müssen zusammengefasst sein, damit nicht einzelne Exports erzeugt werden.

```bash
  #Beschaffungsauftrag für Reichelt exportieren
  ./export.py purchase.order --shop=reichelt.de
  #Beschaffungsauftrag PO00012 exportieren
  ./export.py purchase.order 12
```

### - [`nextprodid.py`](nextprodid.py)
Edit the `reserved_ids` entry under `nextprodid` section: This is a array with ranges of numbers, that are reserved for special products. They will not be returned by this script.

Examples:
```python
reserved_ids = []                       # no reserved ids
reserved_ids = [[0, 99]]                # excludes all numbers from 0 to 99 (include)
reserved_ids = [[0, 99], 2000]          # excludes all numbers from 0 to 99 and 2000
reserved_ids = [[0, 99], [900, 1000], [8000, 8100], [9000, 9999]]
					 # this string is applicable for FAU FabLab
					 # 0 - 99 is for excluding everything <100
					 # 900 - 1000 is for mills
					 # 8000 - 8100 is laser material
					 # 9*** is reserved
```
Then simply run:
```bash
./nextprodid.py
# or
./nextprodid.py 10 # for 10 ids
# or
./nextprodid.py 7 --consecutive # for 7 consecutive ids
# or
./nextprodid.py 17 [--consecutive] --oerpcode # for 17 consecutive codes, but print the OERP code for the code generator in multivariant products
# or
./nextprodid.py 17 [--consecutive] --oerpcode # same as above, but also print the list of the ids
```

### - [`ipython-shell.py`](ipython-shell.py)
```bash
  # ipython Shell, um die oerplib api zu nutzen
  ./ipython-shell.py
   > oerp.browse(...)
```

##Webinterface

Make the `public` folder to a web root directory of a webserver and make following files readable / executeable for the webserver:

 - [`public/index.php`](public/index.php)
 - [`config.ini`](config.ini)
 - [`nextprodid.py`](nextprodid.py)
 - [`oerphelper.py`](oerphelper.py)
