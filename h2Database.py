import jaydebeapi
import numpy as np
from tqdm import tqdm

import test
from ASTParser import JavaASTParser

driver = "org.h2.Driver"
url = "jdbc:h2:~/BigCloneBench/database/bcb"
javaPack = "/disk/study/大创项目/toby/h2-1.4.200.jar"
conn = None
cache = {}


def initialization():
    global conn
    conn = jaydebeapi.connect(
        driver,
        url,
        ["sa", ""],
        javaPack
    )


def fetchall(query):
    curs = conn.cursor()
    curs.execute(query)
    return curs.fetchall()


def fetchone(query):
    info = fetchall(query)[0]
    return info


def read_file(functionalities, type, name, start, end):
    parser = JavaASTParser()
    file_name = "../bcb_reduced/{}/{}/{}".format(functionalities, type, name)
    # print("read_file:", file_name, start, end, id)
    with open(file_name, 'r') as fp:
        lines = fp.readlines()
        sample_file = 'public class Main {\n' + ''.join(lines[start - 1:end]) + '}'  # making it complete java
        return parser.parseCode(sample_file)


def cache_file(id, functionalities, name, start, end, type):
    if id not in cache:
        t = read_file(functionalities, type, name, start, end)
        if type == 'sample':
            cache[id] = t
        return t
    else:
        return cache[id]


def generate_pair(is_clone: bool, limit: int = 1000, syntactic_type=3) -> (int, int):
    parser = JavaASTParser()
    pairs = []
    if is_clone:
        pairs_info = fetchall("SELECT t2.*, f2.NAME,f2.STARTLINE,f2.ENDLINE,f2.TYPE "
                              "FROM PUBLIC.FUNCTIONS as f2,"
                              "(SELECT t1.*, f1.NAME, f1.STARTLINE, f1.ENDLINE, f1.TYPE "
                              "FROM PUBLIC.FUNCTIONS as f1, "
                              "(SELECT FUNCTION_ID_ONE,FUNCTION_ID_TWO,FUNCTIONALITY_ID "
                              "FROM PUBLIC.CLONES "
                              "WHERE TYPE='sample-tagged' and SYNTACTIC_TYPE = %s "
                              "ORDER BY RAND() "
                              "LIMIT %s) as t1 "
                              "WHERE t1.FUNCTION_ID_ONE = f1.ID) as t2 "
                              "WHERE t2.FUNCTION_ID_TWO = f2.ID" %
                              (syntactic_type, limit))
    else:
        pairs_info = fetchall("SELECT t2.*, f2.NAME,f2.STARTLINE,f2.ENDLINE,f2.TYPE "
                              "FROM PUBLIC.FUNCTIONS as f2,"
                              "(SELECT t1.*, f1.NAME, f1.STARTLINE, f1.ENDLINE, f1.TYPE "
                              "FROM PUBLIC.FUNCTIONS as f1, "
                              "(SELECT FUNCTION_ID_ONE,FUNCTION_ID_TWO,FUNCTIONALITY_ID "
                              "FROM PUBLIC.FALSE_POSITIVES "
                              "WHERE TYPE='sample-tagged'"
                              "ORDER BY RAND() "
                              "LIMIT %s) as t1 "
                              "WHERE t1.FUNCTION_ID_ONE = f1.ID) as t2 "
                              "WHERE t2.FUNCTION_ID_TWO = f2.ID" %
                              limit)
    for pair_info in tqdm(pairs_info, unit="cmp"):
        try:
            v1 = cache_file(pair_info[0], pair_info[2], pair_info[3], pair_info[4], pair_info[5], pair_info[6])
            v2 = cache_file(pair_info[1], pair_info[2], pair_info[7], pair_info[8], pair_info[9], pair_info[10])
            com = np.array(parser.compareAll(v1, v2)).mean()
            pairs.append(com)
        except Exception as e:
            print("Error:", e)
    return pairs


def generate_study_data():
    same_group_sim = generate_pair(True)
    diff_group_sim = generate_pair(False)
    print(test.similarity_roc(same_group_sim, diff_group_sim, True, True))


if __name__ == '__main__':
    initialization()
    generate_study_data()

# java ast parser: 1000 set
# threshold = 0.866997 TPR = 0.8818 FPR = 0.506 AUC = 0.7435
