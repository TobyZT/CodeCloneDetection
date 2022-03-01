from ASTParser import ASTParser
import numpy as np
import os
import random
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA


def loadData(n):
    path = "ProgramData\\"
    parser = ASTParser()
    fileList = {}
    # 随机选取文件夹
    for root, dirs, _ in os.walk(path):
        random.shuffle(dirs)
        dirs = dirs[0:n]
        for d in dirs:
            for _, _, files in os.walk(os.path.join(root, d)):
                random.shuffle(files)
                files = files[0:30]
                fileList[d] = files

    data = []
    for (d, files) in fileList.items():
        for file in files:
            with open(os.path.join(path, d, file), "r", encoding='ISO-8859-1') as f:
                try:
                    res = parser.parseCode(f.read())
                except Exception:
                    print("parse error:\n", f.read())
                    continue
            # 解析结果求平均得到49维特征向量v
            v = np.array([0 for i in range(49)])
            for x in res.values():
                v = v + np.array(x)
            v = v / len(res)
            data.append([int(d)] + list(v))
    return np.matrix(data)


def cluster(n, data):
    df = np.array(data[:, 1:])  # 第一列为组号，不作为k-means聚类的维度
    estimator = KMeans(n_clusters=n, init='k-means++')
    res = estimator.fit_predict(df)
    label_pred = estimator.labels_
    centroids = estimator.cluster_centers_
    inertia = estimator.inertia_
    # print(res)
    # print(label_pred)
    # print(centroids)
    # print(inertia)

    # 数据降维，以便可视化
    pca = PCA(n_components=2)  # 49d->2d
    pca.fit(df)
    low_d = pca.transform(df)

    # 可视化
    cl = {}
    for i in range(len(data)):
        if cl.get(data[i, 0]) is None:
            cl[data[i, 0]] = [[], []]  # [[x_axis], [y_axis]]
        cl[data[i, 0]][0].append(low_d[i][0])
        cl[data[i, 0]][1].append(low_d[i][1])

    for c in cl.values():
        plt.scatter(c[0], c[1])  # x--c[0], y--c[1]
    plt.show()


if __name__ == '__main__':
    n = 5
    data = loadData(n)
    cluster(n, data)
