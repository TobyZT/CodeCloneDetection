import csv
import json
import random
import numpy as np
from tqdm import tqdm

import test
from ASTParser import JavaASTParser
from metrics import JavaMetricsParser

cache = {}
cache_metrics = {}


# |- This Project
# |  |-...
# |  |-java_test.py
# |- test
#    |-java
#       |- id2sourcecode(dir)
#       |- noclone-pair.csv
#       |- clone-pair-270000.csv

def read_file(id):
    file_name = "../test/java/id2sourcecode/{}.java".format(id)
    with open(file_name, 'r') as fp:
        sample_file = 'public class Main {\n' + fp.read() + '}'  # making it complete java
        return sample_file


def cache_file(id):
    parser = JavaASTParser()
    if id not in cache:
        t = read_file(id)
        res = cache[id] = parser.parseCode(t)
        return res
    else:
        return cache[id]


def cache_file_metrics(id):
    parser = JavaMetricsParser()
    if id not in cache_metrics:
        t = read_file(id)
        parser.parse(t)
        res = cache_metrics[id] = parser.get_array()
        return res
    else:
        return cache_metrics[id]


def my_filter(fun, data):
    res = []
    for x in data:
        if fun(x):
            res.append(x)
    return res


def fetch_pair_random(file, limit=1000, s_type=None):
    with open(file) as f:
        f_csv = csv.reader(f)
        data = list(f_csv)[1:]
        if s_type is not None:
            data = my_filter(lambda x: x[2] == s_type, data)
        f.close()
        return random.sample(data, limit)


def generate_pair_csv_metrics(mean, std, s_type=None):
    parser = JavaMetricsParser()
    pairs = []
    if s_type is None:  # Non clones
        pairs_info = fetch_pair_random('../test/java/noclone-pair.csv', 2000, s_type=None)
    else:
        pairs_info = fetch_pair_random('../test/java/clone-pair-270000.csv', 2000, s_type=s_type)
    for pair_info in tqdm(pairs_info, unit="cmp"):
        try:
            v1 = cache_file_metrics(pair_info[0])
            v2 = cache_file_metrics(pair_info[1])
            pairs.append(parser.similarity(v1, v2, mean, std))
        except Exception as e:
            print("Error:", e)
    return pairs


def generate_pair_csv(s_type=None):
    parser = JavaASTParser()
    pairs = []
    if s_type is None:  # Non clones
        pairs_info = fetch_pair_random('../test/java/noclone-pair.csv', s_type=None)
    else:
        pairs_info = fetch_pair_random('../test/java/clone-pair-270000.csv', s_type=s_type)
    for pair_info in tqdm(pairs_info, unit="cmp"):
        try:
            v1 = cache_file(pair_info[0])
            v2 = cache_file(pair_info[1])
            com = np.array(parser.compareAll(v1, v2)).mean()
            pairs.append(com)
        except Exception as e:
            print("Error:", e)
    return pairs


def generate_normalize_data_metrics():
    sample_pairs = fetch_pair_random('../test/java/clone-pair-270000.csv', 5000)
    sample = []
    for pair in tqdm(sample_pairs, unit="cmp"):
        try:
            parser = JavaMetricsParser()
            parser.parse(read_file(pair[0]))
            sample.append(parser.get_array())
            parser = JavaMetricsParser()
            parser.parse(read_file(pair[1]))
            sample.append(parser.get_array())
        except Exception as e:
            print("Error:", e)
    sample_mean = np.mean(sample, axis=0)
    sample_std = np.std(sample, axis=0)
    return sample_mean, sample_std


def generate_study_data():
    Pair_type = 'ST3'
    sample_mean, sample_std = generate_normalize_data_metrics()
    diff_group_sim = generate_pair_csv_metrics(sample_mean, sample_std)
    same_group_sim = generate_pair_csv_metrics(sample_mean, sample_std, Pair_type)
    threshold, thresholds_tpr, thresholds_fpr, thresholds = test.similarity_roc(same_group_sim, diff_group_sim, True,
                                                                                True)
    precision = []
    for i in range(0,thresholds_fpr.size):
        precision.append(thresholds_tpr[i] / (thresholds_fpr[i] + thresholds_tpr[i] + 0.0001))
    metrics = {
        "threshold": threshold,
        "precision": precision,
        "thresholds": thresholds.tolist(),
        "means": sample_mean.tolist(),
        "std": sample_std.tolist(),
    }
    diff_group_sim = generate_pair_csv()
    same_group_sim = generate_pair_csv(Pair_type)
    threshold2, thresholds2_tpr, thresholds2_fpr, thresholds2 = test.similarity_roc(same_group_sim, diff_group_sim,
                                                                                    True, True)
    precision = []
    for i in range(0,thresholds2_fpr.size):
        precision.append(thresholds2_tpr[i] / (thresholds2_fpr[i] + thresholds2_tpr[i] + 0.0001))
    ast = {
        "threshold": threshold2,
        "precision": precision,
        "thresholds": thresholds2.tolist(),
    }
    file = open("threshold_setting.json", "w")
    file.write(json.dumps({
        "metrics": metrics,
        "ast": ast,
    }))


if __name__ == '__main__':
    generate_study_data()

# java ast parser: 1000 set
# threshold = 0.866997 TPR = 0.8818 FPR = 0.506 AUC = 0.7435
