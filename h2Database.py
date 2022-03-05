import jaydebeapi

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


def cache_sample():
    sample_files = fetchall("SELECT NAME,STARTLINE,ENDLINE,ID FROM PUBLIC.FUNCTIONS WHERE TYPE='sample'")
    for sample in sample_files:
        file_name = "../bcb_reduced/2/sample/{}".format(sample[0])
        with open(file_name, 'r') as fp:
            lines = fp.readlines()
            sample_file = ''.join(lines[sample[1] - 1:sample[2]])
            cache[sample[3]] = sample_file


def cache_tagged(functionalities, type, name, start, end, id):
    file_name = "../bcb_reduced/{}/{}/{}".format(functionalities, type, name)
    with open(file_name, 'r') as fp:
        lines = fp.readlines()
        sample_file = ''.join(lines[start - 1:end])
        cache[id] = sample_file


def generate_pair(is_clone: bool, limit: int = 1000, syntactic_type=3) -> (int, int):
    pairs = []
    if is_clone:
        pairs_info = fetchall("SELECT t1.*, NAME, STARTLINE, ENDLINE, TYPE "
                              "FROM PUBLIC.FUNCTIONS, "
                              "(SELECT FUNCTION_ID_ONE,FUNCTION_ID_TWO,FUNCTIONALITY_ID "
                              "FROM PUBLIC.CLONES "
                              "WHERE TYPE='sample-tagged' and SYNTACTIC_TYPE = %s "
                              "ORDER BY RAND() "
                              "LIMIT %s) as t1 "
                              "WHERE t1.FUNCTION_ID_ONE = ID " %
                              (syntactic_type, limit))
    else:
        pairs_info = fetchall("SELECT t1.*, NAME, STARTLINE, ENDLINE, TYPE "
                              "FROM PUBLIC.FUNCTIONS, "
                              "(SELECT FUNCTION_ID_ONE,FUNCTION_ID_TWO,FUNCTIONALITY_ID "
                              "FROM PUBLIC.CLONES "
                              "WHERE TYPE='sample-tagged' "
                              "ORDER BY RAND() "
                              "LIMIT %s) as t1 "
                              "WHERE t1.FUNCTION_ID_ONE = ID " %
                              limit)
    i = 0
    for pair_info in pairs_info:
        i = i + 1
        pairs.append((pair_info[0], pair_info[1]))
        cache_tagged(pair_info[2], pair_info[6], pair_info[3], pair_info[4], pair_info[5], pair_info[0])
        if i % 100 == 0:
            print(i)
    return pairs


def generate_study_data():
    tp_set = generate_pair(True)
    fp_set = generate_pair(False)
    pass


if __name__ == '__main__':
    initialization()
    cache_sample()
    generate_study_data()
