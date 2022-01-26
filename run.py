from ASTParser import ASTParser
import numpy as np
import os
import time
import random

if __name__ == '__main__':
    # 同一文件夹
    path = "ProgramData\\"
    parser = ASTParser()
    log = open("log.txt", "w")
    for i in range(1, 30):
        for root, dirs, files in os.walk(path + str(i)):
            t1 = time.time()
            # 随机选取12个两两比较，计算平均相似度
            random.shuffle(files)
            files = files[0:12]
            res = []
            for index, file in enumerate(files[:len(files) - 1]):
                with open(os.path.join(root, file), "r", encoding='ISO-8859-1') as f:
                    v1 = parser.parseCode(f.read())
                for nextFile in files[index + 1:]:
                    with open(os.path.join(root, nextFile), "r", encoding='ISO-8859-1') as f:
                        v2 = parser.parseCode(f.read())
                    com = np.array(parser.compareAll(v1, v2)).mean()  # 取平均
                    res.append(com)

            t2 = time.time()

            print("第{}段计算完成，用时{:.2f}s".format(i, t2 - t1))
            log.write("第{}段计算完成，用时{:.2f}s\n".format(i, t2 - t1))
            log.write(str(res) + "\n")
            log.write("平均相似度" + str(sum(res) / len(res)) + "\n")
            log.write("---------------------------\n")
