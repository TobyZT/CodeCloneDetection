import csv
import random
import numpy as np
from tqdm import tqdm

import test
from ASTParser import JavaASTParser

cache = {}


# |- This Project
# |  |-...
# |  |-java_test.py
# |- test
#    |-java
#       |- id2sourcecode(dir)
#       |- noclone-pair.csv
#       |- clone-pair-270000.csv

def read_file(id):
    parser = JavaASTParser()
    file_name = "../test/java/id2sourcecode/{}.java".format(id)
    with open(file_name, 'r') as fp:
        sample_file = 'public class Main {\n' + fp.read() + '}'  # making it complete java
        return parser.parseCode(sample_file)


def cache_file(id):
    if id not in cache:
        t = read_file(id)
        cache[id] = t
        return t
    else:
        return cache[id]


def my_filter(fun, data):
    res = []
    for x in data:
        if fun(x):
            res.append(x)
    return res


def fetch_pair_random(file, limit=100, s_type=None):
    with open(file) as f:
        f_csv = csv.reader(f)
        data = list(f_csv)[1:]
        if s_type is not None:
            data = my_filter(lambda x: x[2] == s_type, data)
        f.close()
        return random.sample(data, limit)


def generate_pair_csv(s_type=None):
    parser = JavaASTParser()
    pairs = []
    if s_type is None:  # Non clones
        pairs_info = fetch_pair_random('../test/java/noclone-pair.csv', s_type=None)
    else:
        pairs_info = fetch_pair_random('../test/java/clone-pair-270000.csv', s_type=s_type)
    for pair_info in tqdm(pairs_info, unit="cmp"):
        try:
            v1 = read_file(pair_info[0])
            v2 = read_file(pair_info[1])
            com = np.array(parser.compareAll(v1, v2)).mean()
            pairs.append(com)
        except Exception as e:
            print("Error:", e)
    return pairs


def generate_study_data():
    diff_group_sim = generate_pair_csv()
    same_group_sim = generate_pair_csv('T1')
    print(test.similarity_roc(same_group_sim, diff_group_sim, True, True))


if __name__ == '__main__':
    generate_study_data()

# java ast parser: 1000 set
# threshold = 0.866997 TPR = 0.8818 FPR = 0.506 AUC = 0.7435
