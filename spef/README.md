# SPEF (student project evaluation framework)

### Požiadavky na spustenie
* python 3.10+
* pyyaml 6.0+
* pygments 2.12.0+
* jinja2 3.1.2+
* docker

Pred spustením je potreba vložiť nový štýl pre zvýraznenie syntaxe do pygments:
```
pygments_dir=`python -c 'import pygments as _; print(_.__path__[0])'`
cp src/ncurses.py $pygments_dir/styles/
```

### Spustenie frameworku
* `run.sh`

### Spustenie testov
* `prepare_tests.sh` (ak nie je vytvorený Docker image 'test')
* `run_tests.sh`

### Adresárová štruktúra zdrojových kódov
* `example/` obsahuje ukážkový adresár projektu
* `src/` obsahuje zdrojové kódy systému
* `tests/` obsahuje integračné testy systému
* `prepare_tests.sh` vytvorí Docker image 'test' potrebný pre spustenie integračných testov
* `run.sh` spustí framework
* `run_tests.sh` spustí integračné testy


### Ukážkový adresár projektu
V adresári `example` je založený ukážkový projekt pre vyskúšanie frameworku. Adresár obsahuje:
* študentské riešenia (archívy, ktoré treba rozbaliť),
* testy v pod-adresári `tests`,
* testovaciu stratégiu v súbore `tests/testsuite.sh`,
* Dockerfile pre vytvorenie docker imagu na testovanie,
* upravený konfiguračný súbor projektu.
Autor testov a súboru tradelog: Aleš Smrčka