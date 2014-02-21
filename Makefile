.PHONY: all clean deps

all: test dist/lottery.rdf.xml

dev: 
	python setup.py develop

clean:
	rm -rf dist/

test:
	py.test --flakes lottery_rdf/

dist/lottery.rdf.xml:
	mkdir -p dist/
	python bin/dump.py dist/lottery.rdf.xml
