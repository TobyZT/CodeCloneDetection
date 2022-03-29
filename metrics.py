import re
import sys
from math import log2

import javalang.parse
import numpy as np
from abc import ABCMeta, abstractmethod

import numpy as np

sys.path.extend(['.', '..'])

operators = ['!=', '!', '%=', '%', '&&', '&=', '&', '||', '|=', '|', '(', ')', '*=', '*', '++', '+=', '+', '--', '-=',
             '->', '-', '...', '.', '/=', '/', '::', ':', '<<=', '<<', '<=', '<', '==', '=', '>>=', '>=', '>>', '>',
             '?', '[', ']', '^=', '^', '{', '}', '~', ',', ';']


class JavaMetricsParser:
    XMET = 0  # external method called FINISH
    LMET = 0  # local method called FINISH
    NEXP = 0  # expressions
    LOOP = 0  # loops (for,while) FINISH
    NOS = 0  # statement
    NOA = 0  # arguments FINISH
    MDN = 0  # maximum depth of nesting FINISH
    VDEC = 0  # variables declared
    VREF = 0  # variables referenced
    NCLTRL = 0  # Character literals
    NSLTRL = 0  # string literals
    NNLTRL = 0  # Numerical literals
    NBLTRL = 0  # Boolean literals
    NOPR = 0  # operators
    NAND = 0  # operand
    HVOC = 0  # Halstead vocabulary
    HEFF = 0  # Halstead effort to implement
    HDIF = 0  # Halstead difficulty to implement
    _current_MDN = 0  # current MDN
    _method_cache = None

    def __init__(self, **kwargs):
        self.operands = dict()
        self.operators = dict()
        self.local_function = list()
        pass

    def visit(self, node):
        """ Visit a node.
        """

        if self._method_cache is None:
            self._method_cache = {}

        visitor = self._method_cache.get(node.__class__.__name__, None)
        if visitor is None:
            method = 'visit_' + node.__class__.__name__
            visitor = getattr(self, method, self.generic_visit)
            if visitor is None:
                return
            self._method_cache[node.__class__.__name__] = visitor

        return visitor(node)

    def visit_MethodDeclaration(self, node):
        self.local_function.append(node.name)
        self.generic_visit(node)

    def visit_MethodInvocation(self, node):
        # print('Function Call %s called at %s' % (node.name.name, node.name.coord))
        if node.member in self.local_function:
            self.LMET += 1
        else:
            self.XMET += 1
        self.generic_visit(node)

    def visit_BlockStatement(self, node):
        self._current_MDN += 1
        # print("Enter Block level %d" % self._current_MDN)
        self.MDN = max(self.MDN, self._current_MDN)
        self.generic_visit(node)
        # print("Leave Block level %d" % self._current_MDN)
        self._current_MDN -= 1

    def visit_VariableDeclaration(self, node):
        # print("Variable declared %s at %s" % (node.name, node.coord))
        self.VDEC += 1
        self.generic_visit(node)

    def visit_MemberReference(self, node):
        # print("Variable referenced %s at %s" % (node.name, node.coord))
        self.VREF += 1
        self.generic_visit(node)

    def visit_Literal(self, node):
        if node.value == 'true':
            self.NBLTRL += 1  # boolean literal
        elif node.value[0] == '"' and node.value[-1] == '"':
            self.NSLTRL += 1  # string literal
        elif node.value[0] == '\'' and node.value[-1] == '\'':
            self.NCLTRL += 1  # char literal
        else:
            self.NNLTRL += 1

    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.compareAll(
        """
        if type(node) == 'NoneType':
            return

        if isinstance(node, list) and len(node) == 0:
            return

        if hasattr(node, 'arguments'):
            self.NOA += 1

        node_name = node.__class__.__name__
        if 'Statement' in node_name:
            self.NOS += 1
            if node_name in ['ForStatement', 'WhileStatement', 'DoStatement']:
                self.LOOP += 1
        elif 'Expression' in node_name or node_name == 'Assignment':
            self.NEXP += 1
        elif node_name == "MemberReference":
            if node.postfix_operators is not None:
                self.NEXP += len(node.postfix_operators)
            if node.prefix_operators is not None:
                self.NEXP += len(node.prefix_operators)

        if hasattr(node, 'children'):
            # print(node.__class__.__name__)
            for child in node.children:
                if child.__class__.__name__ not in ['str', 'NoneType', 'set']:
                    self.visit(child)

        if isinstance(node, list):
            for child in node:
                if child.__class__.__name__ not in ['str', 'NoneType', 'set']:
                    self.visit(child)

    def parse_halstead(self, code):
        lines = code.split('\n')
        for line in lines:
            pattern = re.compile(r'"(?:[^"]|\\")*[^\\]"')
            for s in pattern.findall(line):
                if s == ' ':
                    continue
                if s in self.operands:
                    self.operands[s] = self.operands[s] + 1
                else:
                    self.operands[s] = 1
            line = re.sub(pattern, ' ', line)

            # match operators
            for key in operators:
                self.operators[key] = self.operators.get(key, 0) + line.count(key)
                line = line.replace(key, ' ')

            # match operands
            for token in line.split():
                if token == ' ':
                    continue
                if token in self.operands:
                    self.operands[token] = self.operands[token] + 1
                else:
                    self.operands[token] = 1

        n1, N1, n2, N2 = 0, 0, 0, 0

        # print("OPERATORS:\n")
        for key in self.operators.keys():
            if self.operators[key] > 0 and key not in ")}]":
                n1, N1 = n1 + 1, N1 + self.operators[key]
                # print("{} = {}".format(key, self.operators[key]))

        # print("\nOPERANDS\n")
        for key in self.operands.keys():
            if self.operands[key] > 0:
                n2, N2 = n2 + 1, N2 + self.operands[key]
                # print("{} = {}".format(key, self.operands[key]))

        self.NOPR = N1
        self.NAND = N2
        self.HVOC = N1 + N2
        self.HDIF = n1 * N2 / 2 / n2
        self.HEFF = self.HDIF * (N1 + N2) * log2(n1 + n2)

    def parse(self, code):

        ast = javalang.parse.parse(code)

        self.visit(ast)
        self.parse_halstead(code)

    def get_array(self) -> np.ndarray:
        return np.array(self.output_array())

    def output_dict(self):
        return {
            "XMET": self.XMET,
            "LMET": self.LMET,
            "NEXP": self.NEXP,
            "LOOP": self.LOOP,
            "NOS": self.NOS,
            "NOA": self.NOA,
            "MDN": self.MDN,
            "VDEC": self.VDEC,
            "VREF": self.VREF,
            "NCLTRL": self.NCLTRL,
            "NSLTRL": self.NSLTRL,
            "NNLTRL": self.NNLTRL,
            "NOPR": self.NOPR,
            "NAND": self.NAND,
            "HVOC": self.HVOC,
            "HEFF": self.HEFF,
            "HDIF": self.HDIF
        }

    def output_array(self):
        return [
            self.XMET,
            self.LMET,
            self.NEXP,
            self.LOOP,
            self.NOS,
            self.NOA,
            self.MDN,
            self.VDEC,
            self.VREF,
            self.NCLTRL,
            self.NSLTRL,
            self.NNLTRL,
            self.NOPR,
            self.NAND,
            self.HVOC,
            self.HEFF,
            self.HDIF
        ]

    @staticmethod
    def similarity(arr1, arr2, mean, std) -> float:
        arr1 = (arr1 - mean) / std
        arr2 = (arr2 - mean) / std
        correlation = np.corrcoef(arr1, arr2)
        return correlation[0][1]
