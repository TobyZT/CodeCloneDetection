import sys
import re
from math import log2

if len(sys.argv) != 2:
    print("Usage: python3 halstead.py name_of_program")
    exit()

operatorsFileName = "operators"
programFileName = sys.argv[1]

operators = {}
operands = {}

with open(operatorsFileName) as f:
    for op in f:
        operators[op.replace('\n', '')] = 0

isComment = False

with open(programFileName) as f:
    for line in f:
        line = line.strip("\n").strip(' ')

        if line.startswith("/*"):
            isComment = True

        if (not line.startswith("//")) and (not isComment) and (not line.startswith('#')):
            # match string constant
            pattern = re.compile(r'"(?:[^"]|\\")*[^\\]"')
            for s in pattern.findall(line):
                if s == ' ':
                    continue
                if s in operands:
                    operands[s] = operands[s] + 1
                else:
                    operands[s] = 1
            line = re.sub(pattern, ' ', line)

            # match operators
            for key in operators.keys():
                operators[key] = operators[key] + line.count(key)
                line = line.replace(key, ' ')

            # match operands
            for token in line.split():
                if token == ' ':
                    continue
                if token in operands:
                    operands[token] = operands[token] + 1
                else:
                    operands[token] = 1

        if line.endswith("*/"):
            isComment = False

n1, N1, n2, N2 = 0, 0, 0, 0

print("OPERATORS:\n")
for key in operators:
    if operators[key] > 0 and key not in ")}]":
        n1, N1 = n1 + 1, N1 + operators[key]
        print("{} = {}".format(key, operators[key]))

print("\nOPERANDS\n")
for key in operands.keys():
    if operands[key] > 0:
        n2, N2 = n2 + 1, N2 + operands[key]
        print("{} = {}".format(key, operands[key]))

val = {"N": N1 + N2, "n": n1 + n2, "V": (N1 + N2) * log2(n1 + n2), "D": n1 * N2 / 2 / n2}
val['E'] = val['D'] * val['V']
val['L'] = val['V'] / val['D'] / val['D']
val['I'] = val['V'] / val['D']
val['T'] = val['E'] / 18
val['N^'] = n1 * log2(n1) + n2 * log2(n2)
val['L^'] = 2 * n2 / N2 / n1

unit = {'V': 'bits', 'T': 'seconds'}
name = {'N': 'Halstead Program Length', 'n': 'Halstead Vocabulary', 'V': 'Program Volume', 'D': 'Program Difficulty',
        'E': 'Programming Effort', 'L': 'Language level', 'I': 'Intelligence Content', 'T': 'Programming time',
        'N^': 'Estimated program length', 'L^': 'Estimated language level'}

print("\nThe various values are: ")
for key in val.keys():
    print("{} ({}) = {} {}".format(key, name[key], val[key], unit[key] if key in unit else ''))
