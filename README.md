oerp-tools
==========

Hacky commandlinetools for things that should rather be [OERP](https://github.com/odoo/odoo) plugins.

##Content

 - `export.py`: Exports orders, lists quantity and product ids from orders in oerp.
 - `nextprodid.py`: A small python script, to get the next available numeric product id.
 - `ipython-shell.py`: A ipython shell for the [oerp library](https://pypi.python.org/pypi/OERPLib/)
 - `oerphelper.py`: A helper library for python scripts.
 - `set-logo.py`: Set the company logo (`set-logo.py example-data/logo-testdatenbank.png`)
 - `erpReicheltImport.py`: Imports Reichelt-shoppingcarts into the ERP automagically.

##Dependencies
* [python2.7](https://www.python.org/download/releases/2.7/)
* [ipython](http://ipython.org/)
* [oerplib](https://pypi.python.org/pypi/OERPLib) (`sudo pip install oerplib`)

##Usage
```bash
  git clone --recursive  https://github.com/mgmax/oerp-tool-stuff
  cd oerp-tools
  cp config.ini.example config.ini
  # config.ini anpassen
  # Userlogin dafür verwenden
  # database Namen anpassen an Datenbanknamen (z.B. production)
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
reserved_ids = []                        # no reserved ids
reserved_ids = [[0, 100]]                # excludes all numbers from 0 to 99 (include)
reserved_ids = [[0, 100], [2000, 2001]]  # excludes all numbers from 0 to 99 and 2000
                                         #          (from 2000 to 2001 (excl.) = 2000)
reserved_ids = [[0, 100], [900, 1000], [8000, 8101], [9000, 10000]]
					 # this string is applicable for FAU FabLab
					 # 0 - 99 is for excluding everything <100
					 # 900 - 1000 is for mills
					 # 8000 - 8100 is laser material
					 # 9* is reserved
```
Then simply run:
```bash
./nextprodid.py
```

### - [`ipython-shell.py`](ipython-shell.py)
```bash
  # ipython Shell, um die oerplib api zu nutzen
  ./ipython-shell.py
   > oerp.browse(...)
```

### - [`erpReicheltImport.py`](erpReicheltImport.py)
```bash
  # nicht mehr genutzt, theoretisch funktionsfähig, aber recht fragil:
  # Reichelt-Warenkörbe und -artikel halbwegs automagisch ins ERP importieren
  # ./erpReicheltImport.py basket.txt
```
