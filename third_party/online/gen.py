# -*- coding: utf-8 -*-
from ks3.connection import Connection
from ks3.prefix import Prefix
from ks3.key import Key
import os
import json
import sys

fp = open("conf.json")
conf = json.loads(fp.read())
fp.close()

conn = Connection(conf["access_key"], conf["secret_key"], host=conf["host"])

# 获取存储空间实例
b = conn.get_bucket(conf["bucket"])

# 列举 images 文件夹下的所有文件。比如b.list(prefix="images/")
a = sys.argv[1]
output = sys.argv[2]

def download(root, a):
    keys = b.list(prefix=a)
    for item in keys:
        if isinstance(item, Key):
            k = b.get_key(item.name)
            dst = os.path.join(output, item.name.replace(root, ""))
            k.get_contents_to_filename(dst)
        elif isinstance(item, Prefix):
            dst = os.path.join(output, item.name.replace(root, ""))
            os.makedirs(dst)
            download(root, item.name)

download(a, a)
