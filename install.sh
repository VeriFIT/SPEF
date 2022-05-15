type pip &>/dev/null || { echo 'command pip not found (you have to install pip first)'; exit 1; }

cwd=`pwd`
src=`dirname ${0}`

echo "installing pyyaml..."
pip install pyyaml &>/dev/null

echo "installing jinja2..."
pip install jinja2 &>/dev/null

echo "installing Pygments..."
pip install Pygments &>/dev/null

pygments_dir=`python -c 'import pygments as _; print(_.__path__[0])'`
cp $cwd/$src/ncurses.py $pygments_dir/styles/

