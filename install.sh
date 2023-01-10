cwd=`pwd`
src=`dirname ${0}`

pygments_dir=`python -c 'import pygments as _; print(_.__path__[0])'`
cp $cwd/$src/src/ncurses.py $pygments_dir/styles/

