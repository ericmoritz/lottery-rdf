HYDRA_TMP := $(shell mktemp "/tmp/hydra.owl.XXXX")

.PHONY: all clean deps 

all: test ontologies/hydra.owl dist/resources

upload: dist/resources
	python bin/upload_resources.py dist/resources/

dev: 
	python setup.py develop

clean:
	rm -rf dist/
	rm -f ontologies/hydra.owl

test:
	py.test --flakes lottery_rdf/

dist/resources: 
	mkdir -p dist/resources/
	python bin/serialize_resources.py dist/resources/

ontologies/hydra.owl:
	curl http://www.w3.org/ns/hydra/core | python bin/convert_rdf.py "json-ld" "application/rdf+xml" > $(HYDRA_TMP)
	mv $(HYDRA_TMP) ontologies/hydra.owl
