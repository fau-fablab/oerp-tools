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

  #Reichelt exportieren
  ./erpReicheltImport.py export reichelt.de
  #Pollin exportieren
  ./erpReicheltImport.py export Pollin

  # ipython Shell, um die oerplib api zu nutzen
  ./ipython-shell.py
   > oerp.browse(...)
```
