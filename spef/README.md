# SPEF (student project evaluation framework)

### Požiadavky na spustenie
* python 3.10+
* pyyaml 6.0+
* pygments 2.12.0+
* jinja2 3.1.2+

Pred spustením je potreba vložiť štýl do pygments (kvôli správnemu zvýrazneniu syntaxe):

* pygments_dir=`python -c 'import pygments as _; print(_.__path__[0])'`
* cp src/ncurses.py $pygments_dir/styles/

### Spustenie frameworku
* run.sh
