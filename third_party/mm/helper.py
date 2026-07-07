import click
import os
import glob
import json
import sys
import tempfile
import shutil
import time
import psutil
import traceback
from datetime import datetime
import requests
import zipfile
import hashlib
from PIL import Image
import subprocess
import copy
from evalmm.registry import EVALUATORS, DATASETS
from mmengine.config import Config
from evalmm.server.utils import maybe_register_class

starttime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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


def write_objects(src_path: str, rel_path: str, public: bool = True) -> str:
    rel_path = rel_path.rstrip('/')
    if public and not rel_path.startswith("public"):
        rel_path = os.path.join('public', rel_path)

    base_dir = os.path.join(os.environ['MODEL_PATH'], '__objects__')
    with open(src_path, 'rb') as src_fp:
        with open(os.path.join(base_dir, rel_path), "wb") as dst_fp:
            dst_fp.write(src_fp.read())
    url = f'/objects/{rel_path}'
    return url


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

def write(path, idx, batch_id, result_id, task_name, try_path, output):
    global starttime
    endtime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    res = {"ret": 1, "data": {}, "starttime": starttime, "endtime": endtime, "lbx": 0}
    starttime = endtime
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
        res["lbx"] = s["data"][idx]["data"]["lbx"]
        if s["data"][idx]["data"]["lbx"] == 1:
            res["parent"] = s["data"][idx]["data"]["parent"]
        if s["try_run"]:
            res["dataset"] = s["data"][idx]["data"]["dataset"]
            # 图问答
            if s["data"][idx]["data"]["name"] == "图问答":
                answers = {}
                fp = open(try_path, "r")
                s0 = fp.read()
                data = json.loads(s0)
                for item in data:
                    answers[item["question_id"]] = item["answer"]
                fp.close()

                ct = get_task(idx)
                cfg = Config.fromfile(ct, lazy_import=False)
                maybe_register_class(cfg, ct)
                cfg.dataset.debug=True
                print(cfg)
                dataset = DATASETS.build(cfg.dataset)
                annotation = dataset.get_annotation()
                for k, v in annotation.items():
                    if not "img_path" in v:
                        v["img_path"] = v.get("images", None)
                result0 = []
                for k, v in answers.items():
                    path = ""
                    if annotation[k]["img_path"] is not None:
                        if isinstance(annotation[k]["img_path"], list):
                            for path in annotation[k]["img_path"]:
                                path = os.path.join(dataset.data_root, path)
                                break
                        elif annotation[k]["img_path"] is not None:
                            path = os.path.join(dataset.data_root, annotation[k]["img_path"])
                    if path == "":
                        continue
                    cur = copy.deepcopy(annotation[k])
                    md5 = upload(path)
                    cur["md5"] = md5
                    del cur["img_path"]
                    cur["label"] = cur.get("answer", "")
                    cur["answer"] = v
                    result0.append(cur)
                    if len(result0) == 5:
                        res["data"] = result0
                        break
            # 文本生成图像
            elif s["data"][idx]["data"]["dataset"].find("文本生成图像") > -1:
                answers = {}
                for root, dirs, files in os.walk(output):
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
            # 图像-文本匹配
            elif s["data"][idx]["data"]["dataset"].find("图像-文本匹配") > -1:
                res["data"] = []
                for root, dirs, files in os.walk(output):
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
            if s["data"][idx]["data"].get("subjective", 0) == 1:
                mulu = os.path.basename(output)
                dst = f"result/{s['batch_id']}/{mulu}"
                for filename in os.listdir(output):
                    cur = f"{dst}/{filename}"
                    write_objects(os.path.join(output, filename), cur)
            elif "save" in s["data"][idx]["data"] and s["data"][idx]["data"]["save"] == 1:
                if s["data"][idx]["data"]["name"] == "t2v":
                    for filename in os.listdir(output):
                            if filename.find("_info") > -1:
                                file_path = os.path.join(output, filename)
                                fp = open(file_path, "r")
                                data = json.loads(fp.read())
                                fp.close()
                                res0 = []
                                for item in data:
                                    rel_path = f"public/save/{s['data'][args.idx]['id']}/{item['video_path']}"
                                    src_path = os.path.join(args.output, item["video_path"])
                                    url = write_objects(src_path, rel_path)
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
                                dst = f"save/{s['data'][args.idx]['id']}/lb.json"
                                res['url'] = write_objects(cur_path, dst)
                                break
                else:
                    src = f'{s["data"][idx]["data"]["dataset_show"]}.{s["data"][idx]["id"]}.zip'
                    with zipfile.ZipFile(src, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(output):
                            for file in files:
                                file_path = os.path.join(root, file)
                                zipf.write(file_path, os.path.relpath(file_path, output))

                    dst = f"save/{s['data'][idx]['id']}/{src}"
                    res["url"] = write_objects(src, dst)
                    os.remove(src)

    except Exception as ex:
        traceback.print_exc()
        res["ret"] = -1
    path = f"batch-{batch_id}-status.json"
    fp = open(get_path(path), "r")
    s = fp.read()
    fp.close()
    data = json.loads(s)
    data["data"][result_id] = res
    write_result(path, data)

@click.group()
def cli():
    pass

def get_task(i):
    fp = open("config.json", "r")
    a = json.loads(fp.read())
    fp.close()
    item = a["data"][i]
    cur = item["data"]["dataset"]
    return cur

@cli.command()
def tasks():
    fp = open("config.json", "r")
    a = json.loads(fp.read())
    fp.close()
    res = ""
    for item in a["data"]:
        if item["status"] == 0 and (not (item["data"]["name"] == "文本生成图像"
            or item["data"]["name"] == "图像-文本匹配"
            or item["data"]["name"] == "文本-图像匹配")):
            cur = item["data"]["dataset"].replace("paneval/", "")
            res += cur + " "
    print(res)

@cli.command()
def tasks_ti():
    fp = open("config.json", "r")
    a = json.loads(fp.read())
    fp.close()
    res = ""
    for item in a["data"]:
        if item["status"] == 0 and (item["data"]["name"] == "文本生成图像"
            or item["data"]["name"] == "图像-文本匹配"
            or item["data"]["name"] == "文本-图像匹配"):
            cur = item["data"]["dataset"].replace("paneval/", "")
            res += cur + " "
    print(res)

@cli.command()
def tasks1():
    fp = open("config.json", "r")
    a = json.loads(fp.read())
    fp.close()
    res = ""
    for item in a["data"]:
        if item["status"] == 0:
            cur = "__paneval__/" + item["data"]["dataset"]
            res += cur + " "
    print(res)

@cli.command()
def online():
    fp = open("config.json", "r")
    a = json.loads(fp.read())
    fp.close()
    if "url" in a:
        print("1")
    else:
        print("0")

@cli.command()
def tryrun():
    fp = open("config.json", "r")
    a = json.loads(fp.read())
    fp.close()
    if a["try_run"]:
       print("--try-run")

@cli.command()
def batchid():
    fp = open("config.json", "r")
    a = json.loads(fp.read())
    fp.close()
    write_result("batch-"+str(a["batch_id"])+"-status.json", {"status": "R", "data": {}})

    fp = open("../meta.json", "r")
    a0 = json.loads(fp.read())
    fp.close()
    for k, v in a.get("online_property", {}).items():
        a0[k] = v
    f = open("../meta.json", "w")
    f.write(json.dumps(a0, ensure_ascii=False, indent=2))
    f.close()
    print(a["batch_id"])

def get_meta():
    if 'MODEL_PATH' in os.environ:
        meta_json_path = os.path.join(os.environ['MODEL_PATH'], 'meta.json')
    else:
        meta_json_path = 'meta.json'

    if not os.path.exists(meta_json_path):
        return {}

    with open(meta_json_path) as f:
        return json.load(f)

@cli.command
def nlp_pretrained():
    meta = get_meta()
    pretrained = meta['pretrained_model_path']
    if pretrained.startswith('./'):
        click.echo(os.path.abspath(os.path.join(os.environ['MODEL_PATH'], pretrained)))
    else:
        parts = pretrained.split('/')
        if len(parts) != 2:
            raise ValueError(f'Unknown format of pretrained model: {pretrained}')
        click.echo(pretrained)

@cli.command()
def adapter():
    try:
        fp = open("../meta.json", "r")
        s = fp.read()
        fp.close()
        s = json.loads(s)
        if "local_path" in s:
            print(s["local_path"])
        elif "url" in s:
            print("")
        else:
            print(os.path.abspath("../checkpoint.pth"))
    except Exception as ex:
        traceback.print_exc()
        print(os.path.abspath("../checkpoint.pth"))

@cli.command()
@click.argument("outputs", required=True)
@click.argument("pid", required=True)
@click.argument("port", required=True)
@click.argument("log_path", required=True)
def output(outputs, pid, port, log_path):
    fp = open("config.json", "r")
    s = fp.read()
    fp.close()
    s = json.loads(s)
    ss = {}
    batch_id = s["batch_id"]
    for i in range(len(s["data"])):
        item = s["data"][i]
        cfg = Config.fromfile(item["data"]["dataset"], lazy_import=False)
        cfg.dataset.debug=True
        r = requests.get(f"http://127.0.0.1:{port}/meta_info?task={cfg.dataset.name}").json()
        print("= = kuakan", r)
        # status 状态。0: 启动，1 成功，-1 失败，2 运行中，3 取消, 99 待推理
        ss[item["data"]["dataset"]] = {"status": 0, "idx": i, "id": item["id"], "total": r.get("length", r.get("video_number", 0))}
    running = True
    pid = int(pid)
    print("= = pid is ", pid)
    keys = list(ss.keys())
    while running:
        if not psutil.pid_exists(pid):
            time.sleep(7)
            try:
                r = requests.get(f"http://127.0.0.1:{port}/eval_finished")
                print("= = server status", r.text)
                if r.json()["status"] == 1:
                    running = False
            except:
                traceback.print_exc()
                running = False
        print("= = running is ", pid, running, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        for k, v in ss.items():
            cfg = Config.fromfile(k, lazy_import=False)
            cfg.dataset.debug=True
            cur = os.path.join(outputs, cfg.dataset.name)
            cur0 = cur
            if os.path.exists(cur) and os.path.exists(os.path.join(cur, "task_info.json")):
                file_list = glob.glob(f"{cur}/*_result.json")
                cur = ""
                for file in file_list:
                    cur = file
                    break
                if cur != "":
                    if v["status"] != 1:
                        time.sleep(2)
                        write(file, v["idx"], batch_id, v["id"], item, os.path.join(outputs, cfg.dataset.name, f"{cfg.dataset.name}.json"), cur0)
                        v["status"] = 1
                elif v["status"] != 1:
                    if v["status"] != 2:
                        res = {"ret": 2, "total": v["total"]}
                        path = f"batch-{batch_id}-status.json"
                        fp = open(get_path(path), "r")
                        s = fp.read()
                        fp.close()
                        data = json.loads(s)
                        data["data"][v["id"]] = res
                        write_result(path, data)
                        v["status"] = 2
                if v["status"] == 2:
                    cmd = f"""cat {log_path} | grep "GET /get_data" | grep "{cfg.dataset.name}" | tail -n 1""" + """ | awk -F "=" '{print $2}' | awk -F "&" '{print $1}'"""
                    result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                    try:
                        curi = int(result.stdout)
                    except:
                        traceback.print_exc()
                        curi = -1
                    v["progress"] = curi + 1
                    path = f"batch-{batch_id}-status.json"
                    fp = open(get_path(path), "r")
                    s = fp.read()
                    fp.close()
                    data = json.loads(s)
                    data["data"][str(v["id"])]["curi"] = v["progress"]
                    write_result(path, data)
        print("= = jia1", pid, ss)
        flag = 0
        for k, v in ss.items():
            if v["status"] == 1 or v["status"] == -1:
                flag += 1
        if flag == len(ss):
            path = f"batch-{batch_id}-status.json"
            fp = open(get_path(path), "r")
            s = fp.read()
            fp.close()
            data = json.loads(s)
            data["status"] = "S"
            write_result(path, data)
            break
        time.sleep(60)

if __name__ == '__main__':
    cli()
