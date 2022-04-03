from cpgqls_client import *
import json

import os
import pydot
import sys


def joern_parse(joern_parse_dir, indir, outdir):
    # indir是源代码目录，joern会解析该目录下的所有源文件
    # joern_parse_dir是joern-parse所在的目录，一般为joern根目录
    # outdir是解析生成的bin文件的目录

    ret = os.system(
        f'sh {joern_parse_dir} {indir} -o {outdir} >/dev/null 2>&1')
    if ret != 0:
        print("joern parsing failed!")
        sys.exit(0)


def import_souce(client, file_path):
    # file_path为需要导入的bin文件路径
    # 该函数执行完之后，cpg被加载进joern server

    # query = open_query(file_path) 考虑兼容性，使用下面的查询指令
    query = f'importCpg(\"{file_path}\")'
    try:
        result = client.execute(query)
        if result['stderr'].find('java') != -1:
            print('joern server error:'+result['stderr'])
            sys.exit(0)
    except Exception as e:
        print("import souce nodes failed!")
        print(e)
        sys.exit(0)


def get_all_nodes(client, node_list_path):
    # node_list_path 存储所有结点的文件路径
    # 该函数返回一个字典，其key为结点id，内容为joern导出的对应结点信息的字典
    query = f"cpg.all.toJson |>\"{node_list_path}\""
    try:
        result = client.execute(query)
        if result['stderr'].find('java') != -1:
            print('joern server error:'+result['stderr'])
            sys.exit(0)
        with open(node_list_path)as f:
            node_list = json.load(f)
        id2node = dict()  # 该字典使用id作为key,对应结点信息作为内容

        for i in range(len(node_list)):
            node = node_list[i]
            # 将结点的id全部改成字符串类型，主要是igraph直接使用数字id会出bug
            node['id'] = str(node['id'])
            id2node[str(node['id'])] = node
        return id2node

    except Exception as e:
        print("getting all nodes failed!")
        print(e)
        sys.exit(0)


def get_all_dotfile(client, raw_dir, dotfile_path, id2node):
    # raw_dir 源代码目录，用来过滤库函数的pdg
    # dotpdg_path 生成的存储dot文件的json文件路径
    # 该函数返回个字典，key:函数id 内容：该函数的pdg dot

    query = f"cpg.method.filter(node=>node.filename.contains(\"{raw_dir}\"))\
    .filterNot(node => node.name.contains(\"<\"))\
    .filterNot(node => node.lineNumber==node.lineNumberEnd)\
    .filterNot(node => node.lineNumber==None)\
    .filterNot(node => node.lineNumberEnd==None)\
    .filterNot(node => node.columnNumber==None)\
    .filterNot(node => node.columnNumberEnd==None)\
    .map(node => List(node.id,node.dotPdg.l)).toJson |>\"{dotfile_path}\""
    # query = f"cpg.method.map(c => (c.id,c.dotPdg.toJson)).toJson |>\"{dotpdg_path}\""
    # print(query)
    try:
        result = client.execute(query)
        # print('client:'+result['stderr'])
        if result['stderr'].find('java') != -1:
            print('joern server error:'+result['stderr'])
            sys.exit(0)

        with open(dotfile_path)as f:
            dot_list = json.load(f)
        pdg_dict = dict()

        for i in range(len(dot_list)):
            dot = dot_list[i]
            func_id = str(dot[0])
            # if ('columnNumber' in id2node[func_id]) == False or ('lineNumber' in id2node[func_id]) == False:
            # continue  # 过滤没有行号或列号的函数的pdg或ast
            dotpdg_str = dot[1][0]
            dot_pdg = pydot.graph_from_dot_data(dotpdg_str)[0]
            if dot_pdg != None:
                pdg_dict[func_id] = dot_pdg
        return pdg_dict

    except Exception as e:
        print("getting all dot file failed!")
        print(e)
        sys.exit(0)


def generate_pdg(joern_client):
    # 所有结点id以字符串形式存储，这是因为从dot文件中解析出来的id是字符串形式的
    joern_parse_dir = '/opt/joern/joern-cli/joern-parse'  # 需根据自己的环境进行修改

    cwd_dir = os.getcwd() + '/slice'
    raw_dir = cwd_dir+"/raw"  # 源文件目录,需手动创建

    # 中间文件目录，包括bin文件、pdg dot、calllee信息和所有结点的json文件
    intermediate_dir = cwd_dir+"/intermediate"

    bin_path = intermediate_dir+"/cpg.bin"  # bin文件路径
    joern_parse(joern_parse_dir, raw_dir, bin_path)  # 生成bin文件

    import_souce(joern_client, bin_path)  # 导入bin文件到服务器

    node_list_path = intermediate_dir + "/allnodes.json"  # 存储所有结点的json文件
    id2node = get_all_nodes(joern_client, node_list_path)

    dot_list_path = intermediate_dir+"/dot.json"  # 存储所有 pdg dot的json文件
    pdg_dict = get_all_dotfile(joern_client, raw_dir, dot_list_path, id2node)

    res = {}
    for pdg_id, pdg in pdg_dict.items():
        edge_list = []
        filename = os.path.split(id2node[pdg_id]['filename'])[1]
        nodes = pdg.get_nodes()
        edges = pdg.get_edges()
        if len(nodes) == 0:
            return -1

        # for node in nodes:
        #     name = node.get_name()
        #     name = name[1:len(name)-1]
        #     print(name, ": ", id2node[name]['code'])

        # 加入所有边
        for edge in edges:
            start_node_id = json.loads(edge.get_source())
            end_node_id = json.loads(edge.get_destination())
            lineno_st = id2node[start_node_id]['lineNumber']
            lineno_end = id2node[end_node_id]['lineNumber']
            edge_list.append((lineno_st, lineno_end))
            # print("line %s to %s" % (lineno_st, lineno_end))
        res[filename] = edge_list
    return res
