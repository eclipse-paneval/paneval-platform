# -*- coding: utf-8 -*-
import json
import sys
import argparse
import tempfile
import os
import shutil
from ks3.connection import Connection
import requests
import traceback
import hashlib
import numpy as np
from PIL import Image
import zipfile
import psutil
import time
from datetime import datetime

'''

{
    "function": "insert",
    "data": {
        "name": "文生视频",
        "parentName": "",
        "meta_data": {
            "data": [
                {
                    "name": "t2v",
                    "dataset": "configs/t2v/sora_prompt.py",
                    "output": "t2v_output/sora_prompt",
                    "dataset_show": "sora_prompt"
                }
            ]
        }
    }
}


{
    "function": "insert",
    "data": {
        "name": "文本生成图像",
        "parentName": "",
        "meta_data": {
            "data": [
                {
                    "name": "t2i",
                    "dataset": "configs/t2i/coco.py",
                    "output": "t2i_output/coco",
                    "dataset_show": "coco"
                },
                {
                    "name": "t2i",
                    "dataset": "configs/t2i/cub.py",
                    "output": "t2i_output/cub",
                    "dataset_show": "cub"
                },
                {
                    "name": "t2i",
                    "dataset": "configs/t2i/flowers.py",
                    "output": "t2i_output/flowers",
                    "dataset_show": "flowers"
                }
            ]
        }
    }
}

{
    "function": "insert",
    "data": {
        "name": "图像-文本匹配",
        "parentName": "",
        "meta_data": {
            "data": [
                {
                    "name": "retrieval",
                    "dataset": "configs/retrieval/coco.py",
                    "output": "retrieval_output/coco",
                    "dataset_show": "coco"
                },
                {
                    "name": "retrieval",
                    "dataset": "configs/retrieval/f30k.py",
                    "output": "retrieval_output/f30k",
                    "dataset_show": "f30k"
                }
            ]
        }
    }
}

'''

parser = argparse.ArgumentParser()
parser.add_argument('--func', type=str, help='功能，有: gen, write, batch_id, get_task, 缺省是gen', default="gen")
parser.add_argument('--data', type=str, default="", help='信息，缺省是""')
parser.add_argument('--path', type=str, default="", help='')
parser.add_argument('--output', type=str, default="", help='')
parser.add_argument('--idx', type=int, default=0, help='')
parser.add_argument('--starttime', type=str, default="", help='开始时间')
parser.add_argument('--endtime', type=str, default="", help='结束时间')
args = parser.parse_args()

fanyi = {
    "accuracy/top1": "Top-1 Accuracy",
    "accuracy/top5": "Top-5 Accuracy",
    "delta1": "δ1",
    "delta2": "δ2",
    "delta3": "δ3",
    "abs_rel": "Abs Rel",
    "rms": "RMSE",
    "sq_rel": "Sq Rel",
    "log_rms": "RMSE Log",
    "retrieval/Recall@1": "Top-1 Recall",
    "retrieval/Recall@10": "Top-10 Recall",
    "retrieval/Recall@100": "Top-100 Recall",
    "retrieval/Recall@1000": "Top-1000 Recall",
    "retrieval/Recall@4": "Top-4 Recall",
    "retrieval/Recall@16": "Top-16 Recall",
    "retrieval/Recall@32": "Top-32 Recall",
}

def upload(path):
    dir = os.path.join(os.environ['OUTPUT_DIR'], "imgdata")
    if not os.path.exists(dir):
        os.makedirs(dir)
    md5 = hashlib.md5(path.encode()).hexdigest()
    dst = os.path.join(dir, md5)
    if not os.path.exists(dst):
        img = Image.open(path)
        width, height = img.size
        maxX = 384.0
        if width > maxX or height > maxX:
            if width > height:
                height = maxX * height / width
                width = maxX
            else:
                width = maxX * width / height
                height = maxX
            img = img.resize((int(width), int(height)))
        img.convert("RGB").save(dst, format="JPEG")
        os.chmod(dst, 0o644)
    return md5

def get_path(name: str) -> str:
    prefix = os.environ['OUTPUT_PREFIX']
    return os.path.join(os.environ['OUTPUT_DIR'], f'{prefix}{name}')

def write_result(name: str, results):
    result_path = get_path(name)
    f = tempfile.NamedTemporaryFile('w', delete=False)
    json.dump(results, f, ensure_ascii=False, indent=2)
    f.close()
    os.chmod(f.name, 0o644)
    shutil.move(f.name, result_path)

def write(path, idx, batch_id, result_id, task_name, try_path):
    endtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    res = {"ret": 1, "data": {}, "starttime": args.starttime, "endtime": endtime, "lbx": 0}
    args.starttime = endtime
    try:
        fp = open(path, "r")
        log = fp.read()
        fp.close()
        s = json.loads(log)
        res["data"] = s

        fp = open("config.json", "r")
        s = fp.read()
        fp.close()
        s = json.loads(s)
        if "lbx" in s["data"][idx]["data"]:
            res["lbx"] = s["data"][idx]["data"]["lbx"]
            res["parent"] = s["data"][idx]["data"]["parent"]
        if s["try_run"]:
            res["dataset"] = s["data"][args.idx]["data"]["dataset"]
            # 图问答
            if s["data"][args.idx]["data"]["dataset"].find("vqa") > -1:
                answers = {}
                fp = open(try_path, "r")
                s0 = fp.read()
                data = json.loads(s0)
                for item in data:
                    answers[item["question_id"]] = item["answer"]
                fp.close()

                r = requests.get("http://127.0.0.1:5000/meta_info?task=" + task_name)
                data = json.loads(r.text)
                result0 = []
                for i in range(data["length"]):
                    r = requests.get("http://127.0.0.1:5000/get_data?index=" + str(i) + "&task=" + task_name)
                    cur = json.loads(r.text)
                    if cur["question_id"] in answers:
                        md5 = upload(cur["img_path"][0])
                        del cur["img_path"]
                        cur["md5"] = md5
                        cur["answer"] = answers[cur["question_id"]]
                        result0.append(cur)
                        if len(result0) == 5:
                            res["data"] = result0
                            break
            # 文本生成图像
            elif s["data"][args.idx]["data"]["dataset"].find("t2i") > -1:
                answers = {}
                for root, dirs, files in os.walk(args.output):
                    for file in files:
                        if file.find("_result") == -1:
                            file_path = os.path.join(root, file)
                            answers[file.split(".")[0]] = file_path
                r = requests.get("http://127.0.0.1:5000/meta_info?task=" + task_name)
                data = json.loads(r.text)
                result0 = []
                for i in range(data["length"]):
                    r = requests.get("http://127.0.0.1:5000/get_data?index=" + str(i) + "&task=" + task_name)
                    cur = json.loads(r.text)
                    if str(cur["id"]) in answers:
                        md5 = upload(answers[str(cur["id"])])
                        del cur["id"]
                        cur["md5"] = md5
                        result0.append(cur)
                        if len(result0) == 5:
                            res["data"] = result0
                            break
            # retrieval
            elif s["data"][args.idx]["data"]["dataset"].find("retrieval") > -1:
                res["data"] = []
                for root, dirs, files in os.walk(args.output):
                    for file in files:
                        if file.find("_result") == -1:
                            file_path = os.path.join(root, file)
                            data = np.load(file_path)
                            data = np.argmax(data, axis = 1)
                            for i in range(len(data)):
                                if i == 5:
                                    break
                                r1 = requests.get("http://127.0.0.1:5000/get_data?index="+str(i)+"&type=img&task=" + task_name)
                                r2 = requests.get("http://127.0.0.1:5000/get_data?index="+str(data[i])+"&type=text&task=" + task_name)
                                cur = {"txt": json.loads(r2.text)["caption"], "md5": upload(json.loads(r1.text)["img_path"])}
                                res["data"].append(cur)
                            break
        else:
            if "save" in s["data"][args.idx]["data"] and s["data"][args.idx]["data"]["save"] == 1:
                if s["data"][args.idx]["data"]["name"] == "t2v":
                    for filename in os.listdir(args.output):
                            if filename.find("_info") > -1:
                                file_path = os.path.join(args.output, filename)
                                fp = open(file_path, "r")
                                data = json.loads(fp.read())
                                fp.close()
                                res0 = []
                                ks3 = s["ks3"]
                                conn = Connection(ks3["access_key"], ks3["secret_key"], host=ks3["host"])
                                b = conn.get_bucket(ks3["bucket"])
                                for item in data:
                                    dst = f"{ks3['model_ks3_url']}/save/{s['data'][args.idx]['id']}/{item['video_path']}"
                                    k = b.new_key(dst)
                                    k.set_contents_from_filename(os.path.join(args.output, item["video_path"]), policy="public-read")
                                    url = k.generate_url(3600 * 24 * 365 * 10).replace("ks3-cn-beijing-internal.ksyuncs.com", "ks3-cn-beijing.ksyuncs.com")
                                    item["video_path"] = f"<video width='100%' src='{url}' controls></video>"
                                    res0.append({"data": item})
                                res0 = {
                                    "data": res0,
                                    "xml": """
<View>
  <Style>
    .lsf-hint { display: none; }
  	.lsf-richtext__line{ white-space: pre-wrap; }
  </Style>
  <View>
    <Text name="text-1" value="$prompt" />
    <HyperText name="video_0_0" value="$video_path"/>
    <Text name="txt00" value="请评价总体印象(0-5分)" />
    <Number name="score_0_0" toName="video_0_0" max="5" min="0" slider="true" step="0.01" defaultValue="0"/>
    <HyperText name="h00" value="">
        <hr/>
    </HyperText>
    </View>
    <View>
        <Text name="text-2" value="$prompt" />
        <HyperText name="video_1_4" value="$video_path"/>
        <Text name="txt14" value="请评价图文一致性(0-5分)" />
        <Number name="score_1_4" toName="video_1_4" max="5" min="0" slider="true" step="0.01" defaultValue="0"/>
        <HyperText name="h14" value="">
            <hr/>
        </HyperText>
    </View>
    <View>
        <Text name="text-3" value="$prompt" />
        <HyperText name="video_2_0" value="$video_path"/>
        <Text name="txt20" value="请评价视频真实性(0-5分)" />
        <Number name="score_2_0" toName="video_2_0" max="5" min="0" slider="true" step="0.01" defaultValue="0"/>
        <HyperText name="h20" value="">
            <hr/>
        </HyperText>
    </View>
</View>
"""
                                }
                                cur_path = "lb.json"
                                fp = open(cur_path, "w")
                                fp.write(json.dumps(res0, ensure_ascii=False))
                                fp.close()
                                dst = f"{ks3['model_ks3_url']}/save/{s['data'][args.idx]['id']}/lb.json"
                                k = b.new_key(dst)
                                k.set_contents_from_filename(cur_path, policy="public-read")
                                res["ks3"] = dst
                                break
                else:
                    src = f'{s["data"][args.idx]["data"]["dataset_show"]}.{s["data"][args.idx]["id"]}.zip'
                    with zipfile.ZipFile(src, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(args.output):
                            for file in files:
                                file_path = os.path.join(root, file)
                                zipf.write(file_path, os.path.relpath(file_path, args.output))
                    ks3 = s["ks3"]
                    conn = Connection(ks3["access_key"], ks3["secret_key"], host=ks3["host"])
                    b = conn.get_bucket(ks3["bucket"])
                    dst = f"{ks3['model_ks3_url']}/save/{s['data'][args.idx]['id']}/{src}"
                    k = b.new_key(dst)
                    k.set_contents_from_filename(src, policy="public-read")
                    res["ks3"] = dst
                    os.remove(src)

    except Exception as ex:
        traceback.print_exc()
        res["ret"] = -1
    path = "batch-"+batch_id+"-status.json"
    fp = open(get_path(path), "r")
    s = fp.read()
    fp.close()
    data = json.loads(s)
    data["data"][result_id] = res
    write_result(path, data)

if args.func == "tasks":
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    tasks = ""
    for item in s["data"]:
        tasks += item["data"]["dataset"] + " "
    print(tasks)
elif args.func == "get_status":
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    ss = {}
    batch_id = args.data
    pid = int(args.path)
    for i in range(len(s["data"])):
        item = s["data"][i]
        # status 状态。0: 启动，1 成功，-1 失败，2 运行中，3 取消, 99 待推理
        ss[item["data"]["output"].split("/")[1]] = {"status": 0, "idx": i, "id": item["id"]}
    outputs = "outputs"
    running = True
    while running:
        if not psutil.pid_exists(pid):
            r = requests.get("http://127.0.0.1:5000/eval_finished")
            if r.json()["status"] == 1:
                running = False
        for item in os.listdir(outputs):
            file = os.path.join(outputs, item, f"{item}_result.json")
            if os.path.exists(file):
                if ss[item]["status"] != 1:
                    time.sleep(2)
                    args.output = os.path.join(outputs, item)
                    write(file, ss[item]["idx"], batch_id, ss[item]["id"], item, os.path.join(outputs, item, f"{item}.json"))
                    ss[item]["status"] = 1
            elif ss[item]["status"] != 1:
                if ss[item]["status"] != 2:
                    res = {"ret": 2}
                    path = "batch-"+batch_id+"-status.json"
                    fp = open(get_path(path), "r")
                    s = fp.read()
                    fp.close()
                    data = json.loads(s)
                    data["data"][ss[item]["id"]] = res
                    write_result(path, data)
                    ss[item]["status"] = 2
        flag = 0
        for k, v in ss.items():
            if v["status"] == 1 or v["status"] == -1:
                flag += 1
        if flag == len(ss):
            path = "batch-"+batch_id+"-status.json"
            fp = open(get_path(path), "r")
            s = fp.read()
            fp.close()
            data = json.loads(s)
            data["status"] = "S"
            write_result(path, data)
            break
        time.sleep(3)
elif args.func == "output":
    idx = int(args.data)
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    if idx >= len(s["data"]):
        sys.exit(0)

    data = s["data"][idx]
    res0 = data["data"]
    print(res0["output"])
elif args.func == "get_checkpoint":
    try:
        fp = open("../meta.json", "r")
        s = fp.read()
        fp.close()
        s = json.loads(s)
        if "local_path" in s:
            print(s["local_path"])
        elif "base_url" in s:
            print("")
        else:
            print(os.path.abspath("../checkpoint.pth"))
    except Exception as ex:
        traceback.print_exc()
        print(os.path.abspath("../checkpoint.pth"))
elif args.func == "eva_name":
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    print(s["eva_name"])
elif args.func == "get_name":
    idx = int(args.data)
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    if idx >= len(s["data"]):
        sys.exit(0)

    data = s["data"][idx]
    res0 = data["data"]
    print(res0["name"])
elif args.func == "data_root":
    idx = int(args.data)
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    if idx >= len(s["data"]):
        sys.exit(0)
    data = s["data"][idx]
    res0 = data["data"]
    print(res0["data_root"])
elif args.func == "data_root_path":
    idx = int(args.data)
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    if idx >= len(s["data"]):
        sys.exit(0)
    data = s["data"][idx]
    res0 = data["data"]
    print(res0["data_root_path"])
elif args.func == "lbx":
    idx = int(args.data)
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    if idx >= len(s["data"]):
        sys.exit(0)
    lbx = 0
    data = s["data"][idx]
    res0 = data["data"]
    if "lbx" in res0:
        lbx= res0["lbx"]
    print(lbx)
elif args.func == "get_task":
    idx = int(args.data)
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    if idx >= len(s["data"]):
        sys.exit(0)

    data = s["data"][idx]
    res0 = data["data"]
    print(res0["dataset"])
elif args.func == "batch_id":
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    batch_id = s["batch_id"]
    # 写入"status": "R"，这样paneval读的时候就知道，status在running了，前端也会展示
    write_result("batch-"+str(batch_id)+"-status.json", {"status": "R", "data": {}})
    print(batch_id)
elif args.func == "try_run":
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    try_run = s["try_run"]
    if try_run:
        print("--try-run")
    else:
        print("")
elif args.func == "write_cancel": #运行完毕，写入结果
    # 此时args.data是batch_id, args.path是cvtaskresult的id
    res = {"ret": 3, "data": {}}
    path = "batch-"+args.data+"-status.json"
    fp = open(get_path(path), "r")
    s = fp.read()
    fp.close()
    data = json.loads(s)
    data["data"][args.path] = res
    write_result(path, data)
elif args.func == "running": #运行完毕，写入结果
    # 此时args.data是batch_id, args.path是cvtaskresult的id
    res = {"ret": 2}
    path = "batch-"+args.data+"-status.json"
    fp = open(get_path(path), "r")
    s = fp.read()
    fp.close()
    data = json.loads(s)
    data["data"][args.path] = res
    write_result(path, data)
elif args.func == "end":
    path = "batch-"+args.data+"-status.json"
    fp = open(get_path(path), "r")
    s = fp.read()
    fp.close()
    data = json.loads(s)
    data["status"] = "S"
    write_result(path, data)
