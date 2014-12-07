oerp-tools
==========

##Dependencies
* python2.7
* ipython
* oerplib (`sudo pip install oerplib`)

##Usage
Angebote müssen zusammengefasst sein, damit nicht einzelne Exports erzeugt werden.
```bash
  git clone --recursive  https://github.com/mgmax/oerp-tool-stuff
  cd oerp-tool-stuff
  cp config.ini.example config.ini
  # config.ini anpassen
  # Userlogin dafür verwenden
  # database Namen anpassen an Datenbanknamen (z.B. production)

  #Beschaffungsauftrag für Reichelt exportieren
  ./export.py purchase.order --shop=reichelt.de
  #Beschaffungsauftrag PO00012 exportieren
  ./export.py purchase.order 12

  # nicht mehr genutzt, theoretisch funktionsfähig, aber recht fragil:
  # Reichelt-Warenkörbe und -artikel halbwegs automagisch ins ERP importieren
  # ./erpReicheltImport.py basket.txt

  # ipython Shell, um die oerplib api zu nutzen
  ./ipython-shell.py
   > oerp.browse(...)
```
