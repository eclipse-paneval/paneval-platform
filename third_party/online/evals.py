import json
import sys

with open(sys.argv[1], 'r') as fp:
    a = json.loads(fp.read())
    print(a['evals'])
