import sys
import networkx as nx
from pycparser import c_parser
import numpy as np
import zss
import re

from test import *

sys.path.extend(['.', '..'])


class ASTParser:
    typeNum = 0
    typeNames = []
    vector = []
    edge_list = []
    func_list = []
    var_list = []

    def __init__(self):
        self.parser = c_parser.CParser()
        self.G = nx.Graph()
        with open("token_type.cfg", "r") as f:
            lines = f.readlines()
            # typeNames = ['ArrayDecl', 'ArrayRef', ... ]
            self.typeNames = [x.rstrip() for x in lines]
            self.typeNum = len(self.typeNames)
        self.G.add_nodes_from(self.typeNames)

    def traverse(self, root):
        if len(root.children()) == 0:
            return
        for (_, child) in root.children():
            self.edge_list.append([root.__class__.__name__, child.__class__.__name__])
            self.traverse(child)

    def parseCode(self, code):
        # preprocess:
        code = re.sub('(?<!:)\\/\\/.*|\\/\\*(\\s|.)*?\\*\\/', "", code).strip()
        ast = self.parser.parse(code)

        # clear results of last parsing
        self.edge_list.clear()
        self.var_list.clear()
        self.func_list.clear()
        self.G.clear_edges()
        self.traverse(ast)

        # add edges to graph
        for [u, v] in self.edge_list:
            if self.G.has_edge(u, v):
                self.G[u][v]['weight'] += 1
            else:
                self.G.add_edge(u, v, weight=1)

        # calculate featured vector
        res = {}
        res['harmonicCent'] = [cent / len(self.G) if cent > 1e-5 else 0 for cent in
                               nx.harmonic_centrality(self.G).values()]
        res['eigenvectorCent'] = [cent if cent > 1e-5 else 0 for cent in nx.eigenvector_centrality(self.G).values()]
        res['closenessCent'] = [cent if cent > 1e-5 else 0 for cent in nx.closeness_centrality(self.G).values()]
        res['betweennessCent'] = [cent if cent > 1e-5 else 0 for cent in nx.betweenness_centrality(self.G).values()]

        # self.vector = [cent if cent > 1e-5 else 0 for cent in v.values()]
        return res

    @staticmethod
    def compare(vec1, vec2):
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        # 计算相关系数
        correlation = np.corrcoef(v1, v2)
        return correlation[0][1]
        # # 计算向量的cosine距离
        # num = float(np.dot(v1, v2))  # 向量点乘
        # denom = np.linalg.norm(v1) * np.linalg.norm(v2)  # 求模长的乘积
        # return 0.5 + 0.5 * (num / denom) if denom != 0 else 0

    @staticmethod
    def compareAll(vec1, vec2):
        # row: cosine correlation
        res = []
        for (key, value) in vec1.items():
            row = []
            v1 = np.array(value)
            v2 = np.array(vec2[key])
            # 计算向量的cosine距离
            num = float(np.dot(v1, v2))  # 向量点乘
            denom = np.linalg.norm(v1) * np.linalg.norm(v2)  # 求模长的乘积
            row.append(0.5 + 0.5 * (num / denom) if denom != 0 else 0)
            # 计算相关系数
            correlation = np.corrcoef(v1, v2)
            row.append(correlation[0][1])
            # # 计算曼哈顿距离
            # manhattan = sum(abs(v1 - v2)) / len(v1)
            # row.append(manhattan)
            # # 计算切比雪夫距离
            # chebyshev = abs(v1 - v2).max()
            # row.append(chebyshev)
            # 结果加入一行
            res.append(row)
        return res


if __name__ == '__main__':
    p = ASTParser()
    v1 = p.parseCode(text1)
    v2 = p.parseCode(text2)
    v3 = p.parseCode(text3)

    v4 = p.parseCode(code1)
    v5 = p.parseCode(code2)

    for (key, value) in v4.items():
        print(key + " similarity 4 - 5: ", p.compare(value, v5[key]))
    print('----------')

    for (key, value) in v1.items():
        print(key + " similarity 1 - 2: ", p.compare(value, v2[key]))
    print('----------')
    for (key, value) in v1.items():
        print(key + " similarity 1 - 3: ", p.compare(value, v3[key]))
    print('-----------')
    for (key, value) in v2.items():
        print(key + " similarity 2 - 3: ", p.compare(value, v3[key]))
