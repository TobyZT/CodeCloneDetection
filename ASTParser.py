import os
import re
import sys

import clang.cindex
import javalang
import networkx as nx
import numpy as np
from pycparser import c_parser

sys.path.extend(['.', '..'])


class ASTParser:
    typeNum = 0
    typeNames = ['ArrayDecl', 'ArrayRef', 'Assignment', 'Alignas', 'BinaryOp', 'Break', 'Case', 'Cast', 'Compound',
                 'CompoundLiteral', 'Constant', 'Continue', 'Decl', 'DeclList', 'Default', 'DoWhile',
                 'EllipsisParam', 'EmptyStatement', 'Enum', 'Enumerator', 'EnumeratorList', 'ExprList', 'FileAST',
                 'For', 'FuncCall', 'FuncDecl', 'FuncDef', 'Goto', 'ID', 'IdentifierType', 'If', 'InitList',
                 'Label', 'NamedInitializer', 'ParamList', 'PtrDecl', 'Return', 'StaticAssert', 'Struct',
                 'StructRef', 'Switch', 'TernaryOp', 'TypeDecl', 'Typedef', 'Typename', 'UnaryOp', 'Union', 'While',
                 'Pragma']
    vector = []
    edge_list = []

    def __init__(self):
        self.G = nx.DiGraph()
        # with open("token_type.cfg", "r") as f:
        #     lines = f.readlines()
        #     # typeNames = ['ArrayDecl', 'ArrayRef', ... ]
        #     self.typeNames = [x.rstrip() for x in lines]
        self.typeNum = len(self.typeNames)
        self.G.add_nodes_from(self.typeNames)

    def traverse(self, root):
        if len(root.children()) == 0:
            return
        for (_, child) in root.children():
            self.edge_list.append(
                [root.__class__.__name__, child.__class__.__name__])
            self.traverse(child)

    def parseCode(self, code):
        # preprocess:
        code = re.sub(r'(?<!:)\/\/.*|\/\*(\s|.)*?\*\/',
                      "", code).strip()  # strip comments
        code = re.sub(r'^#.+$', "", code, flags=re.M).strip()  # strip macro

        parser = c_parser.CParser()
        ast = parser.parse(code)

        # clear results of last parsing
        self.edge_list.clear()
        self.G.clear_edges()
        # traver AST
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
        # res['eigenvectorCent'] = [cent if cent > 1e-5 else 0 for cent in nx.eigenvector_centrality(self.G).values()]
        res['degreeCent'] = [cent if cent >
                             1e-5 else 0 for cent in nx.degree_centrality(self.G).values()]
        res['closenessCent'] = [cent if cent >
                                1e-5 else 0 for cent in nx.closeness_centrality(self.G).values()]
        res['betweennessCent'] = [cent if cent >
                                  1e-5 else 0 for cent in nx.betweenness_centrality(self.G).values()]

        # self.vector = [cent if cent > 1e-5 else 0 for cent in v.values()]
        return res

    @staticmethod
    def compare(vec1, vec2):
        # column: cosine correlation
        res = []
        for (key, value) in vec1.items():
            row = []
            v1 = np.array(value)
            v2 = np.array(vec2[key])
            if np.all(v1 == v2):
                res.append([1, 1])
                continue
            if np.all(v1 == 0) or np.all(v2 == 0):
                res.append([0, 0])
                continue
            # 计算向量的cosine距离
            num = float(np.dot(v1, v2))  # 向量点乘
            denom = np.linalg.norm(v1) * np.linalg.norm(v2)  # 求模长的乘积
            row.append(0.5 + 0.5 * (num / denom) if denom != 0 else 0)
            # 计算相关系数
            correlation = np.corrcoef(v1, v2)
            row.append(correlation[0][1])
            res.append(row)
        return res


class CppASTParser(ASTParser):
    typeNames = []
    file_path = ""

    def __init__(self):
        self.typeNames = [
            x.name for x in clang.cindex.CursorKind.get_all_kinds() if x is not None]
        super().__init__()
        # clang.cindex.Config.set_library_file(clang_path)
        self.index = clang.cindex.Index.create()

    def traverse(self, node):
        # if node.location.file is not None:
        #     if node.location.file.name == self.file_path:
        #         print('Found %s [line=%s, col=%s, kind=%s]' % (
        #             node.displayname, node.location.line, node.location.column, node.kind.name))
        for child in node.get_children():
            if child.location.file is not None:
                if child.location.file.name == self.file_path:
                    self.edge_list.append([node.kind.name, child.kind.name])
            self.traverse(child)

    def parseCode(self, path):
        tu = self.index.parse(path, args=['-x', 'c++'])
        root = tu.cursor
        self.file_path = root.displayname

        self.edge_list.clear()
        self.G.clear_edges()
        self.traverse(root)

        for [u, v] in self.edge_list:
            if self.G.has_edge(u, v):
                self.G[u][v]['weight'] += 1
            else:
                self.G.add_edge(u, v, weight=1)

        # calculate featured vector
        res = {}
        res['harmonicCent'] = [cent / len(self.G) if cent > 1e-5 else 0 for cent in
                               nx.harmonic_centrality(self.G).values()]
        # res['eigenvectorCent'] = [cent if cent > 1e-5 else 0 for cent in nx.eigenvector_centrality(self.G).values()]
        res['degreeCent'] = [cent if cent >
                             1e-5 else 0 for cent in nx.degree_centrality(self.G).values()]
        res['closenessCent'] = [cent if cent >
                                1e-5 else 0 for cent in nx.closeness_centrality(self.G).values()]
        res['betweennessCent'] = [cent if cent >
                                  1e-5 else 0 for cent in nx.betweenness_centrality(self.G).values()]

        # self.vector = [cent if cent > 1e-5 else 0 for cent in v.values()]
        return res


class JavaASTParser(ASTParser):
    typeNames = ["CompilationUnit", "Import", "Documented", "Declaration", "TypeDeclaration", "PackageDeclaration",
                 "ClassDeclaration", "EnumDeclaration", "InterfaceDeclaration", "AnnotationDeclaration", "Type",
                 "BasicType", "ReferenceType", "TypeArgument", "TypeParameter", "Annotation", "ElementValuePair",
                 "ElementArrayValue", "Member", "MethodDeclaration", "FieldDeclaration", "ConstructorDeclaration",
                 "ConstantDeclaration", "ArrayInitializer", "VariableDeclaration", "LocalVariableDeclaration",
                 "VariableDeclarator", "FormalParameter", "InferredFormalParameter", "Statement", "IfStatement",
                 "WhileStatement", "DoStatement", "ForStatement", "AssertStatement", "BreakStatement",
                 "ContinueStatement", "ReturnStatement", "ThrowStatement", "SynchronizedStatement", "TryStatement",
                 "SwitchStatement", "BlockStatement", "StatementExpression", "TryResource", "CatchClause",
                 "CatchClauseParameter", "SwitchStatementCase", "ForControl", "EnhancedForControl", "Expression",
                 "Assignment", "TernaryExpression", "BinaryOperation", "Cast", "MethodReference", "LambdaExpression",
                 "Primary", "Literal", "This", "MemberReference", "Invocation", "ExplicitConstructorInvocation",
                 "SuperConstructorInvocation", "MethodInvocation", "SuperMethodInvocation", "SuperMemberReference",
                 "ArraySelector", "ClassReference", "VoidClassReference", "Creator", "ArrayCreator", "ClassCreator",
                 "InnerClassCreator", "EnumBody", "EnumConstantDeclaration", "AnnotationMethod"]

    def traverse(self, root):
        if isinstance(root, list) and len(root) == 0:
            return

        # print(root.__class__.__name__)

        if hasattr(root, 'children'):
            # print(root.__class__.__name__)
            for child in root.children:
                if hasattr(child, 'children'):
                    self.edge_list.append(
                        [root.__class__.__name__, child.__class__.__name__])
                if child.__class__.__name__ not in ['str', 'NoneType', 'set']:
                    self.traverse(child)

        if isinstance(root, list):
            for child in root:
                if hasattr(child, 'children'):
                    self.edge_list.append(
                        [root.__class__.__name__, child.__class__.__name__])
                if child.__class__.__name__ not in ['str', 'NoneType', 'set']:
                    self.traverse(child)

    def parseCode(self, code):
        # preprocess:
        # code = re.sub(r'(?<!:)\/\/.*|\/\*(\s|.)*?\*\/', "", code).strip()  # strip comments
        # code = re.sub(r'^#.+$', "", code, flags=re.M).strip()  # strip macro

        self.edge_list.clear()
        self.G.clear_edges()

        tree = javalang.parse.parse(code)
        self.traverse(tree)

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
        # res['eigenvectorCent'] = [cent if cent > 1e-5 else 0 for cent in nx.eigenvector_centrality(self.G).values()]
        res['degreeCent'] = [cent if cent >
                             1e-5 else 0 for cent in nx.degree_centrality(self.G).values()]
        res['closenessCent'] = [cent if cent >
                                1e-5 else 0 for cent in nx.closeness_centrality(self.G).values()]
        res['betweennessCent'] = [cent if cent >
                                  1e-5 else 0 for cent in nx.betweenness_centrality(self.G).values()]

        # self.vector = [cent if cent > 1e-5 else 0 for cent in v.values()]
        return res
