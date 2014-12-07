oerp-tools
==========

##Dependencies
* python 2.7
* oerplib (`sudo pip install oerplib`)

##Usage
Angebote müssen zusammengefasst sein, damit nicht einzelne Exports erzeugt werden.
```bash
  git clone --recursive  https://github.com/mgmax/oerp-tool-stuff
  cd oerp-tool-stuff
  cp config.ini.example config.ini
  # config.ini anpassen
  # Userlogin dafür verwenden

  #Reichelt exportieren
  ./erpReicheltImport.py export reichelt.de
  #Pollin exportieren
  ./erpReicheltImport.py export Pollin
```
