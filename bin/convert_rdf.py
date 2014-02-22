from rdflib import Graph
import sys

in_format = sys.argv[1]
out_format = sys.argv[2]

if __name__ == '__main__':
    print Graph().parse(file=sys.stdin, format=in_format).serialize(format=out_format),

