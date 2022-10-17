all:	deb


# create a python source package
.PHONY:	sdist
sdist:
	python setup.py --command-packages=stdeb.command sdist


# create a debian source package
.PHONY:	dsc
dsc:
	python setup.py --command-packages=stdeb.command sdist_dsc


# create a debian binary package
.PHONY:	deb
deb:	clean
	git log --pretty="%cs: %s [%h]" > Changelog
	python setup.py --command-packages=stdeb.command bdist_deb
	-rm -f openmetra_*_all.deb openmetra-*.tar.gz
	ln `ls deb_dist/openmetra_*_all.deb | tail -1` .
	ls -l openmetra_*_all.deb


# install the latest debian package
.PHONY:	debinstall
debinstall: deb
	sudo dpkg -i openmetra_*_all.deb


# create a rpm binary package
.PHONY:	rpm
rpm:	clean
	git log --pretty="%cs: %s [%h]" > Changelog
	python setup.py bdist_rpm
	-rm -f openmetra-*.noarch.rpm
	ln `ls dist/openmetra-*.noarch.rpm | tail -1` .
	ls -l openmetra-*.noarch.rpm


# prepare a clean build
.PHONY:	clean
clean:
	python setup.py clean
	-rm -rf *~ .*~ deb_dist dist *.tar.gz *.egg* build tmp


# removes all build artefacts
.PHONY:	distclean
distclean: clean
	-rm -f *.deb *.rpm

