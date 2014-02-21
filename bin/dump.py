from lottery_rdf.models import dump, Config
import sys
import os

config = Config(os.environ['LOTTERY_IRL'])

dump(config, sys.argv[1])
