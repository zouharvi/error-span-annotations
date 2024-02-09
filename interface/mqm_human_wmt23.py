# wget https://storage.googleapis.com/mt-metrics-eval/mt-metrics-eval-v2.tgz
# and put it in data

import collections
import json
import random

# TODO:
# no need for one person to not see multiple translations of the same document

data_mqm = collections.defaultdict(list)

for line in open("data/mt-metrics-eval-v2/wmt23/human-scores/en-de.mqm.merged.seg.rating", "r"):
    sys, mqm = line.strip().split("\t")
    if mqm == "None":
        mqm = []
    else:
        mqm = json.loads(mqm)["errors"]
    mqm = [
        {
            "start_i": x["start"],
            "end_i": x["end"],
            "severity": x["severity"],
        }
        for x in mqm
    ]
    data_mqm[sys].append({"mqm": mqm})


sources = [
    x.strip() for x in
    open("data/mt-metrics-eval-v2/wmt23/sources/en-de.txt", "r")
]
documents = [
    x.strip().split("\t")[1] for x in
    open("data/mt-metrics-eval-v2/wmt23/documents/en-de.docs", "r")
]

print(len(sources), "sources")
systems = list(data_mqm.keys())
for sys in data_mqm.keys():
    print(len(data_mqm[sys]), "of", sys)
    targets = [
        x.strip() for x in
        open(
            f"data/mt-metrics-eval-v2/wmt23/system-outputs/en-de/{sys}.txt", "r")
    ]
    for seg_i, (obj, target, source, document) in enumerate(zip(data_mqm[sys], targets, sources, documents)):
        obj["documentID"] = document
        obj["sourceID"] = "wmt23.sent"
        obj["targetID"] = f"wmt23.sent.{sys}"
        obj["itemType"] = "TGT" if sys != "refA" else "REF"
        obj["sourceText"] = source
        obj["targetText"] = target
        # essentially source ID
        obj["itemID"] = seg_i
        obj["isCompleteDocument"] = False


# make sure that we have as many sources as all systems
assert all([len(v) == len(sources) for v in data_mqm.values()])

# throw away sys source structure
data_mqm = [
    [val[i] for val in data_mqm.values()]
    for i in range(len(sources))
]

# TODO: use only 200 sentences for now
data_mqm = data_mqm[:200]

r = random.Random(123)

tasks = []

for source_section_i in range(len(data_mqm) // 100):
    source_section_a = 100 * source_section_i
    source_section_b = 100 * (source_section_i + 1)
    data = data_mqm[source_section_a:source_section_b]

    tasks_local = [[] for _ in systems]
    for line in data:
        for sys_i, obj in enumerate(line):
            # TODO do _item and _block matter for anything?
            obj["_item"] = 0
            obj["_block"] = 0
            tasks_local[sys_i].append(obj)

    tasks += tasks_local

print("Created", len(tasks), "tasks because we have", len(systems), "systems")

dump_obj = []
for task_i, task in enumerate(tasks):
    obj = {
        "items": task,
        "task": {
            "batchNo": task_i+1,
            "batchSize": 1,
            "randomSeed": 123456,
            "requiredAnnotations": 1,
            "sourceLanguage": "eng",
            "targetLanguage": "deu"
        }
    }
    dump_obj.append(obj)

# use redundancy of 2 for now
print(f'["eng", "deu", "uniform",  {2*len(systems)*(len(data_mqm)//100)}, {len(systems)*(len(data_mqm)//100)}]')

json.dump(dump_obj, open("data/batches.json", "w"), indent=2)
