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
deb:	distclean
	git log --pretty="%cs: %s [%h]" | > Changelog
	python setup.py --command-packages=stdeb.command bdist_deb
	ln `ls deb_dist/openmetra_*_all.deb | tail -1` .


# install the latest debian package
.PHONY:	debinstall
debinstall:
	sudo dpkg -i `ls deb_dist/openmetra_*_all.deb | tail -1`


# prepare a clean build
.PHONY:	clean
clean:
	python setup.py clean


# removes all build artefacts
.PHONY:	distclean
distclean: clean
	rm -rf *~ .*~ deb_dist dist *.tar.gz *.deb *.egg* build tmp

