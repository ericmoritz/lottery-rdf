from lottery_rdf.external.lottostrategies import dump, Config
import sys
import os

config = Config(os.environ['LOTTERY_IRL'])
dump(config, sys.argv[1])
