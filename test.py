import pycparser.plyparser
from sklearn import preprocessing

from ASTParser import ASTParser, CppASTParser
import numpy as np
import os
import math
import random
from matplotlib import pyplot as plt
from sklearn import metrics as sk_metrics


def getCppSimilarityGroup():
    # 自比较
    path = "ProgramData\\"
    parser = CppASTParser()
    log = open("log1.txt", "w")
    cwd_dir = os.getcwd()
    fileList = {}
    sameGroupSim = []
    differentGroupSim = []

    dirList = os.listdir(path)
    random.shuffle(dirList)
    dirList = dirList[:20]

    # same group compare
    for d in dirList:
        print("Processing Group %s self comparison" % d)
        for root, dirs, files in os.walk(os.path.join(path, d)):
            # 随机选取12个两两比较，计算平均相似度
            random.shuffle(files)
            files = files[0:12]
            sim = []
            for index, file in enumerate(files[:len(files) - 1]):
                # f = open(os.path.join(root, file), "r", encoding='ISO-8859-1')
                try:
                    v1 = parser.parseCode(os.path.join(cwd_dir, root, file))
                except pycparser.plyparser.ParseError:
                    print("Cannot Open File %s" % os.path.join(cwd_dir, root, file))
                    continue
                # f.close()
                for nextFile in files[index + 1:]:
                    # f = open(os.path.join(root, nextFile), "r", encoding='ISO-8859-1')
                    try:
                        v2 = parser.parseCode(os.path.join(cwd_dir, root, nextFile))
                    except pycparser.plyparser.ParseError:
                        print("Cannot Open File %s" % os.path.join(cwd_dir, root, nextFile))
                        continue
                    com = np.array(parser.compareAll(v1, v2)).mean()  # 取平均
                    sameGroupSim.append(com)

    # different group
    for root, dirs, _ in os.walk(path):
        random.shuffle(dirs)
        dirs = dirs[:6]
        for d in dirs:
            for _, _, files in os.walk(os.path.join(cwd_dir, root, d)):
                random.shuffle(files)
                files = files[0:10]
                fileList[d] = files

    visited = set()
    for (d1, files1) in fileList.items():
        for (d2, files2) in fileList.items():
            print("Processing Group %s - Group %s" % (d1, d2))
            if (d1, d2) in visited or d1 == d2:
                continue
            visited.add((d1, d2))
            visited.add((d2, d1))
            sim = []
            for f1 in files1:
                for f2 in files2:
                    # f = open(os.path.join(path, d1, f1), "r", encoding='ISO-8859-1')
                    try:
                        v1 = parser.parseCode(os.path.join(cwd_dir, path, d1, f1))
                    except pycparser.plyparser.ParseError:
                        print("Cannot Open File %s" % os.path.join(cwd_dir, path, d1, f1))
                        continue

                    # f = open(os.path.join(path, d2, f2), "r", encoding='ISO-8859-1')
                    try:
                        # code = f.read()
                        v2 = parser.parseCode(os.path.join(cwd_dir, path, d2, f2))
                    except pycparser.plyparser.ParseError:
                        print("Cannot Open File %s" % os.path.join(cwd_dir, path, d2, f2))
                        continue
                    # f.close()
                    com = np.array(parser.compareAll(v1, v2)).mean()
                    differentGroupSim.append(com)
    return sameGroupSim, differentGroupSim


def getSimilarityGroup():
    # 自比较
    path = "ProgramData\\"
    parser = ASTParser()
    log = open("log1.txt", "w")
    fileList = {}
    sameGroupSim = []
    differentGroupSim = []

    dirList = os.listdir(path)
    random.shuffle(dirList)
    dirList = dirList[:20]

    # same group compare
    for d in dirList:
        print("Processing Group %s self comparison" % d)
        for root, dirs, files in os.walk(os.path.join(path, d)):
            # 随机选取12个两两比较，计算平均相似度
            random.shuffle(files)
            files = files[0:12]
            sim = []
            for index, file in enumerate(files[:len(files) - 1]):
                f = open(os.path.join(root, file), "r", encoding='ISO-8859-1')
                try:
                    code = f.read()
                    v1 = parser.parseCode(code)
                except pycparser.plyparser.ParseError:
                    print("Cannot Open File %s" % os.path.join(root, file))
                    continue
                f.close()
                for nextFile in files[index + 1:]:
                    f = open(os.path.join(root, nextFile), "r", encoding='ISO-8859-1')
                    try:
                        code = f.read()
                        v2 = parser.parseCode(code)
                    except pycparser.plyparser.ParseError:
                        print("Cannot Open File %s" % os.path.join(root, nextFile))
                        continue
                    com = np.array(parser.compareAll(v1, v2)).mean()  # 取平均
                    sameGroupSim.append(com)

    # different group
    for root, dirs, _ in os.walk(path):
        random.shuffle(dirs)
        dirs = dirs[:6]
        for d in dirs:
            for _, _, files in os.walk(os.path.join(root, d)):
                random.shuffle(files)
                files = files[0:10]
                fileList[d] = files

    visited = set()
    for (d1, files1) in fileList.items():
        for (d2, files2) in fileList.items():
            print("Processing Group %s - Group %s" % (d1, d2))
            if (d1, d2) in visited or d1 == d2:
                continue
            visited.add((d1, d2))
            visited.add((d2, d1))
            sim = []
            for f1 in files1:
                for f2 in files2:
                    f = open(os.path.join(path, d1, f1), "r", encoding='ISO-8859-1')
                    try:
                        code = f.read()
                        v1 = parser.parseCode(code)
                    except pycparser.plyparser.ParseError:
                        print("Cannot Open File %s" % os.path.join(path, d1, f1))
                        continue

                    f = open(os.path.join(path, d2, f2), "r", encoding='ISO-8859-1')
                    try:
                        code = f.read()
                        v2 = parser.parseCode(code)
                    except pycparser.plyparser.ParseError:
                        print("Cannot Open File %s" % os.path.join(path, d2, f2))
                        continue
                    f.close()
                    com = np.array(parser.compareAll(v1, v2)).mean()
                    differentGroupSim.append(com)
    return sameGroupSim, differentGroupSim


def similarity_roc(sameGroupSim, differentGroupSim, show_hist=False, show_roc=False, title=''):
    if show_hist:
        plt.hist(np.array(sameGroupSim))
        plt.show()
        plt.hist(np.array(differentGroupSim))
        plt.show()

    y = [1] * len(sameGroupSim) + [0] * len(differentGroupSim)
    score = []
    score.extend(sameGroupSim)
    score.extend(differentGroupSim)
    fpr, tpr, thresholds = sk_metrics.roc_curve(np.array(y), np.array(score))
    auc_score = sk_metrics.auc(fpr, tpr)

    if show_roc:
        plt.figure()
        plt.plot(fpr, tpr)
        plt.show()

    threshold = 0.0
    threshold_dis = 0.0
    threshold_fpr = 0.0
    threshold_tpr = 0.0
    for i in range(0, len(fpr)):
        dis = abs((fpr[i] - tpr[i]) / math.sqrt(2))
        if dis > threshold_dis:
            threshold = thresholds[i]
            threshold_fpr = fpr[i]
            threshold_tpr = tpr[i]
            threshold_dis = dis

    return threshold, tpr, fpr, thresholds


if __name__ == '__main__':
    sameGroupSim, differentGroupSim = getCppSimilarityGroup()
    with open("sim.log", "w") as f:
        f.writelines(str(sameGroupSim))
        f.writelines(str(differentGroupSim))
    res = similarity_roc(sameGroupSim, differentGroupSim, show_roc=True, show_hist=True)
    print("Threshold = %f,TPR = %f, FPR = %f, AUC=%f" % res)
