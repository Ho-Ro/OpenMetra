all:	deb


# create a debian binary package
.PHONY:	deb
deb:
	git log --pretty="%cs: %s [%h]" | tac > Changelog
	python setup.py --command-packages=stdeb.command bdist_deb


# create a debian source package
.PHONY:	dsc
dsc:
	python setup.py --command-packages=stdeb.command sdist_dsc


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
	rm -rf *~ .*~ deb_dist dist *.tar.gz *.egg* build tmp

