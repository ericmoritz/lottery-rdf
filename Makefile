.PHONY: all clean deps

all: test dist/lottery.n3.txt

dev: 
	python setup.py develop

clean:
	rm -rf dist/

test:
	py.test --flakes lottery_rdf/

dist/lottery.n3.txt:
	mkdir -p dist/
	python bin/dump.py dist/lottery.n3.txt $(LOTTERY_IRL)
