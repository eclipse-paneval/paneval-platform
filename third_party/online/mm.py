# -*- coding: utf-8 -*-
import os
import json
import sys

a = sys.argv[1]
output = sys.argv[2]
work_dir = sys.argv[3]
fenv_dir = sys.argv[4]

a = json.load(open(a, "r"))
a = {
    "model_name": a["model_name"],
    "url": a["url"],
    "api_key": a["api_key"],
}
os.system(f"cp {work_dir}/paneval/model_zoo/vlm/api_model/* {fenv_dir}")
f = open(output, "w")
f.write(json.dumps(a, ensure_ascii=False, indent=2))
f.close()
