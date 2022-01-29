from ASTParser import ASTParser
import numpy as np
import os
import random


def runSelfCompare(end):
    # 自比较
    path = "ProgramData\\"
    parser = ASTParser()
    log = open("log1.txt", "w")
    res = {}

    # 随机选取文件夹
    dirList = os.listdir(path)
    random.shuffle(dirList)
    dirList = dirList[0:end]

    for d in dirList:
        for root, dirs, files in os.walk(os.path.join(path, d)):
            # 随机选取12个两两比较，计算平均相似度
            random.shuffle(files)
            files = files[0:10]
            sim = []
            for index, file in enumerate(files[:len(files) - 1]):
                with open(os.path.join(root, file), "r", encoding='ISO-8859-1') as f:
                    v1 = parser.parseCode(f.read())
                for nextFile in files[index + 1:]:
                    with open(os.path.join(root, nextFile), "r", encoding='ISO-8859-1') as f:
                        v2 = parser.parseCode(f.read())
                    com = np.array(parser.compareAll(v1, v2)).mean()  # 取平均
                    sim.append(com)
            res[(d, d)] = sum(sim) / len(sim)
            print((d, d), sum(sim) / len(sim))
            log.write(str((d, d)) + " " + str(sum(sim) / len(sim)) + "\n")
    return res


def runCrossCompare(end):
    # 自比较
    path = "ProgramData\\"
    parser = ASTParser()
    log = open("log2.txt", "w")
    fileList = {}
    res = {}
    # 随机选取文件夹
    for root, dirs, _ in os.walk(path):
        random.shuffle(dirs)
        dirs = dirs[0:end]
        for d in dirs:
            for _, _, files in os.walk(os.path.join(root, d)):
                random.shuffle(files)
                files = files[0:6]
                fileList[d] = files

    visited = set()
    for (d1, files1) in fileList.items():
        for (d2, files2) in fileList.items():
            if (d1, d2) in visited or d1 == d2:
                continue
            visited.add((d1, d2))
            visited.add((d2, d1))
            sim = []
            for f1 in files1:
                for f2 in files2:
                    with open(os.path.join(path, d1, f1), "r", encoding='ISO-8859-1') as f:
                        v1 = parser.parseCode(f.read())
                    with open(os.path.join(path, d2, f2), "r", encoding='ISO-8859-1') as f:
                        v2 = parser.parseCode(f.read())
                    com = np.array(parser.compareAll(v1, v2)).mean()
                    sim.append(com)
            res[(d1, d2)] = sum(sim) / len(sim)
            print((d1, d2), sum(sim) / len(sim))
            log.write(str((d1, d2)) + " " + str(sum(sim) / len(sim)) + "\n")
    return res


def normalize(data):
    vec = data.values()
    r = max(vec) - min(vec)
    minV = min(vec)
    for (key, value) in data.items():
        data[key] = (value - minV) / r


if __name__ == '__main__':
    res = runSelfCompare(50)
    res.update(runCrossCompare(20))
    normalize(res)
    with open("log3.txt", "w") as f:
        for (key, value) in res.items():
            f.write(str(key) + "\t\t" + str(value) + "\n")
    print(res)
