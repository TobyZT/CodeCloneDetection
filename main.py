from webbrowser import get
import pickle
import shutil
import os
import uuid
import json
import numpy as np
import clang
from flask import Flask, request
from ASTParser import ASTParser, CppASTParser, JavaASTParser
from MetricsParser import JavaMetricsParser, MetricsParser
from SignatureParser import SignatureParser

clang.cindex.Config.set_library_file('/usr/lib/llvm-10/lib/libclang-10.so.1')

java_ast_parser = JavaASTParser()
c_ast_parser = ASTParser()
cpp_ast_parser = CppASTParser()

java_metrics_parser = JavaMetricsParser()
c_metrics_parser = MetricsParser()

cpp_sig_parser = SignatureParser()


app = Flask(__name__)


def get_ast_similarity(code1, code2, language='cpp'):

    try:
        if language == 'cpp':
            tmp_dir = os.path.join(os.getcwd(), "code_tmp")
            code1_filename = str(uuid.uuid4()) + ".cpp"
            code2_filename = str(uuid.uuid4()) + ".cpp"
            with open(os.path.join(tmp_dir, code1_filename), "w") as f:
                f.write(code1)
            with open(os.path.join(tmp_dir, code2_filename), "w") as f:
                f.write(code2)
            v1 = cpp_ast_parser.parseCode(
                os.path.join(tmp_dir, code1_filename))
            v2 = cpp_ast_parser.parseCode(
                os.path.join(tmp_dir, code2_filename))
            os.remove(os.path.join(tmp_dir, code1_filename))
            os.remove(os.path.join(tmp_dir, code2_filename))
        elif language == 'c':
            v1 = c_ast_parser.parseCode(code1)
            v2 = c_ast_parser.parseCode(code2)
        elif language == 'java':
            v1 = java_ast_parser.parseCode(code1)
            v2 = java_ast_parser.parseCode(code2)
    except Exception as e:
        print(e)
        return -1  # parse failed

    similarrity = np.array(c_ast_parser.compare(v1, v2)).mean()
    return similarrity


def get_metrics_similarity(code1, code2, language='cpp'):
    std_array = np.array([1 for _ in range(17)])
    try:
        if language == 'cpp':
            # not supported yet
            return -1
        elif language == 'c':
            c_metrics_parser.parse(code1)
            v1 = c_metrics_parser.get_array()
            c_metrics_parser.parse(code2)
            v2 = c_metrics_parser.get_array()
        elif language == 'java':
            java_metrics_parser.parse(code1)
            v1 = java_metrics_parser.get_array()
            java_metrics_parser.parse(code2)
            v2 = java_metrics_parser.get_array()
    except Exception as e:
        print(e)
        return -1  # parse failed

    similarity = c_metrics_parser.similarity(v1, v2, means, std)
    return similarity


def reindexing_similarity(value, mode="metrics"):
    global settings
    thresholds = settings[mode]["thresholds"]
    precision = settings[mode]["precision"]
    for i in range(0, len(thresholds)):
        threshold = thresholds[i]
        if value >= threshold:
            return precision[i]
    return 0


@app.route("/compare", methods=['GET', 'POST'])
def compare():
    '''
    request format: json
    {   
        "language": "java",
        "code1": "str",
        "code2": "str"
    }
    '''
    data = json.loads(request.get_data(as_text=True))
    code1 = data['code1']
    code2 = data['code2']
    lang = data['language']

    # print(code1)
    # print("------")
    # print(code2)
    err_response = {
        'result': False,
        'error': 'parse error'
    }
    try:
        ast_similarity = get_ast_similarity(code1, code2, lang)
        metrics_similarity = get_metrics_similarity(code1, code2, lang)
        ast_similarity = reindexing_similarity(ast_similarity)
        metrics_similarity = reindexing_similarity(metrics_similarity)
        # print(ast_similarity)
        # print(metrics_similarity)
    except Exception as e:
        print(e)
        return json.dumps(err_response), 200, {"Content-Type": "application/json"}

    if ast_similarity < 0 or metrics_similarity < 0:
        return json.dumps(err_response), 200, {"Content-Type": "application/json"}

    similar = bool(ast_similarity >
                   ast_threshold and metrics_similarity > metrics_threshold)
    response = {
        'result': True,
        'data': {
            'similar': similar,
            'ast_similarity': int(ast_similarity*100),
            'metrics_similarity': int(metrics_similarity*100)
        }
    }
    return json.dumps(response), 200, {"Content-Type": "application/json"}


def get_cent_map(cent, hash_set):
    cent_map = {}
    cent_map['harmonicCent'] = [cent['harmonicCent'][hash]/len(hash_set)
                                if hash in cent['harmonicCent'] else 0 for hash in hash_set]
    cent_map['degreeCent'] = [cent['degreeCent'][hash]
                              if hash in cent['degreeCent'] else 0 for hash in hash_set]
    cent_map['closenessCent'] = [cent['closenessCent'][hash]
                                 if hash in cent['closenessCent'] else 0 for hash in hash_set]
    cent_map['betweennessCent'] = [cent['betweennessCent'][hash]
                                   if hash in cent['betweennessCent'] else 0 for hash in hash_set]
    return cent_map


@app.route("/check", methods=['GET', 'POST'])
def check():
    data = json.loads(request.get_data(as_text=True))
    code = data['code']
    try:
        slice = cpp_sig_parser.get_slice(code)
        code_map = cpp_sig_parser.normalize()
        code_hash = cpp_sig_parser.get_hash(code_map)
        cent_data = cpp_sig_parser.get_centrality(slice['code.cpp'], code_hash)
        # clean tmp file
        d, _ = os.path.split(cpp_sig_parser.path)
        shutil.rmtree(d)

        # compare with vul data
        vul_dir = os.path.join(os.getcwd(), "vul", "sig_pkl")
        vul_list = os.listdir(os.path.join(
            os.getcwd(), "vul", "vulnerability"))

        probablilities = []
        for vul in vul_list:
            vul_raw = pickle.load(
                open(os.path.join(vul_dir, vul+"_vul.pkl"), "rb"))
            if len(vul_raw) == 0:
                continue
            vul_data = vul_raw[list(vul_raw.keys())[0]]

            patch_raw = pickle.load(
                open(os.path.join(vul_dir, vul+"_patch.pkl"), "rb"))
            patch_data = patch_raw[list(patch_raw.keys())[0]]

            hash_set = set(vul_data['harmonicCent'].keys()).union(
                patch_data['harmonicCent'].keys())

            cent = get_cent_map(cent_data, hash_set)
            vul_cent = get_cent_map(vul_data, hash_set)
            patch_cent = get_cent_map(patch_data, hash_set)

            sim_with_vul = np.array(
                c_ast_parser.compare(cent, vul_cent)).mean()
            sim_with_path = np.array(
                c_ast_parser.compare(cent, patch_cent)).mean()
            # print("vul %s: %f - %f" % (vul, sim_with_vul, sim_with_path))
            if sim_with_vul > sim_with_path:
                probablilities.append((vul, sim_with_vul))
    except Exception as e:
        print(e)
        err_response = {
            'result': False,
            'error': 'parse error'
        }
        return json.dumps(err_response), 200, {"Content-Type": "application/json"}

    # sort by probablities
    probablilities.sort(key=lambda x: x[1], reverse=True)

    vul_detected = bool(len(probablilities) > 0)
    if probablilities[0][1] < 0.75:
        vul_detected == False

    response = {
        'result': True,
        'data': {
            'vulnerable': vul_detected,
            'vulnerabilityList': [{'name': vul, 'possibility': int(prob*100)} for (vul, prob) in probablilities]
        },
    }
    return json.dumps(response), 200, {"Content-Type": "application/json"}


if __name__ == "__main__":
    # init
    global settings, ast_threshold, metrics_threshold, means, std
    f = open("threshold_setting.json", "r")
    settings = json.loads(f.read())
    ast_threshold = settings['ast']['threshold']
    metrics_threshold = settings['metrics']['threshold']
    means = np.array(settings['metrics']['means'])
    std = np.array(settings['metrics']['std'])

    app.run('0.0.0.0', port=3939)
