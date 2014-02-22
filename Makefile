HYDRA_TMP := $(shell mktemp "/tmp/hydra.owl.XXXX")

.PHONY: all clean deps

all: test dist/lottery.rdf.xml ontologies/hydra.owl

dev: 
	python setup.py develop

clean:
	rm -rf dist/
	rm ontologies/hydra.owl

test:
	py.test --flakes lottery_rdf/

dist/lottery.rdf.xml:
	mkdir -p dist/
	python bin/dump.py dist/lottery.rdf.xml

ontologies/hydra.owl:
	curl http://www.w3.org/ns/hydra/core | python bin/convert_rdf.py "json-ld" "application/rdf+xml" > $(HYDRA_TMP)
	mv $(HYDRA_TMP) ontologies/hydra.owl
