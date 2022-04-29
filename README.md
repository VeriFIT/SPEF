# DP

install.sh

pip install setuptools
pip install jinja2
pip install Pygments
pygments_dir=`python -c 'import pygments as _; print(_.__path__[0])'`
cp src/ncurses.py $pygments_dir/styles/


* `pip install setuptools`
* `pip install jinja2`
* `pip install Pygments`

* treba vlozit ncurses style do pygments
pygments_dir=`python -c 'import pygments as _; print(_.__path__[0])'`
cp src/ncurses.py $pygments_dir/styles/


* `docker build -f Dockerfile -t test .`

sudo mkdir /sys/fs/cgroup/systemd
sudo mount -t cgroup -o none,name=systemd cgroup /sys/fs/cgroup/systemd


Warning:
* The curses package is part of the Python standard library, however, the Windows version of Python doesn't include the curses module. If you're using Windows, you have to run: `pip install windows-curses`
