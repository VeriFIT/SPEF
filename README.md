# DP


* `pip install Pygments`
* `pip install setuptools`

* ak nemas vytvoreny image, loadni vzorovy image z filu:
`cat test.tar.gz | docker load`
* alebo vytvor image zo vzoroveho Dockerfilu (potrebujes pristup na net)
`docker build -f Dockerfile -t test .`
* alebo pridat moznost "create default image"


sudo mkdir /sys/fs/cgroup/systemd
sudo mount -t cgroup -o none,name=systemd cgroup /sys/fs/cgroup/systemd


Warning:
* The curses package is part of the Python standard library, however, the Windows version of Python doesn't include the curses module. If you're using Windows, you have to run: `pip install windows-curses`
