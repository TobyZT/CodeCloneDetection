import pickle
from cpgqls_client import *
from slice import *
import os
import shutil
import uuid
import hashlib
import clang.cindex
import networkx as nx


class SignatureParser:
    path = ""

    def __init__(self):
        '''
        use "sudo apt install clang" and "pip install clang" to set up environment
        run "joern --server" before initialize this class
        '''
        # clang.cindex.Config.set_library_file(clang_path)  # set clang path
        self.index = clang.cindex.Index.create()
        self.joern_client = self.connect_server()  # connect to joern server

    def connect_server(self):
        # 和joern server连接，需提前运行./joern --server
        # 返回值为一个client对象，用于之后与joern server进行交互
        # 端口和用户名密码可修改，参照https://docs.joern.io/server
        server_endpoint = "localhost:8080"
        basic_auth_credentials = ("username", "password")
        return CPGQLSClient(server_endpoint, auth_credentials=basic_auth_credentials)

    def get_slice(self, code, language='cpp'):
        '''
        input code string to parse and get a list of PDG edges
        PDG edge is shown as a tuple like: ( lineNumber, lineNumber )
        '''
        if code == "":
            return

        # write code to file
        cwd_dir = os.getcwd()+"/slice"
        code_dir = cwd_dir+"/raw/test"

        shutil.rmtree(os.path.join(cwd_dir, "graph_db", "test"))
        os.mkdir(os.path.join(cwd_dir, "graph_db", "test"))
        shutil.rmtree(os.path.join(cwd_dir, "intermediate"))
        os.mkdir(os.path.join(cwd_dir, "intermediate"))

        dir = os.path.join(code_dir, str(uuid.uuid4()))
        os.mkdir(dir)
        filename = os.path.join(dir, 'code.'+language)
        self.path = filename
        with open(filename, "w") as f:
            f.write(code)

        # generate PDG
        res = generate_pdg(self.joern_client)
        return res

    def normalize(self, path=""):
        '''
        input path of code file and get normalized code
        if path is empty, path of code in get_slice() method will be used

        the output will be a map of each line of input code and the map key is lineNumber of code.
        '''
        res = {}
        if path == "":
            path = self.path
        tu = self.index.parse(path, args=['-x', 'c++'])

        row = 1
        col = 1
        func_list = []
        param_list = []
        line = ""
        for t in tu.get_tokens(extent=tu.cursor.extent):
            if t.kind.name == 'COMMENT':
                continue
            # print("%s \t\t [line=%d, col=%d, kind=%s, info=%s]" % (
            #     t.spelling, t.location.line, t.location.column, t.kind.name, t.cursor.kind.name))
            # output newline
            if t.location.line > row:
                if line != "":
                    res[row] = line.strip()
                line = ""
                row = t.location.line
                col = 1
            # # first token in a new line
            # if col == 1:
            #     res += t.spelling
            #     col += len(t.spelling)
            #     line = t.location.line
            #     continue

            # output space
            if t.location.column > col:
                line += ' '
                col = t.location.column

            if t.kind.name == 'IDENTIFIER' and t.cursor.kind.name == 'FUNCTION_DECL':
                func_list.append(t.spelling)
            if t.kind.name == 'IDENTIFIER' and t.cursor.kind.name == 'PARM_DECL':
                param_list.append(t.spelling)

            if t.kind.name == 'IDENTIFIER' and t.spelling in func_list:
                line += 'FUNCTION'
            elif t.kind.name == 'IDENTIFIER' and t.spelling in param_list:
                line += 'PARAM'
            elif t.kind.name == 'IDENTIFIER' and t.cursor.kind.name in ['PARM_DECL', 'VAR_DECL', 'DECL_REF_EXPR']:
                line += 'VARIABLE'
            elif t.kind.name == 'IDENTIFIER':
                line += 'VARIABLE'
            else:
                line += t.spelling
            col += len(t.spelling)

        # ouput the last line
        if line != "":
            res[row] = line.strip()

        return res

    def get_hash(self, code_map):
        res = {}
        for lineNumber, line in code_map.items():
            sha = hashlib.sha256()
            sha.update(line.encode())
            res[lineNumber] = sha.hexdigest()[:6]
        return res

    def get_centrality(self, slice, code_hash):
        G = nx.DiGraph()
        G.add_nodes_from(list(code_hash.values()))
        for (u, v) in slice:
            u_hash = code_hash.get(u)
            v_hash = code_hash.get(v)
            if u_hash != None and v_hash != None:
                if G.has_edge(u_hash, v_hash):
                    G[u_hash][v_hash]['weight'] += 1
                else:
                    G.add_edge(u_hash, v_hash, weight=1)

        res = {}
        # harmonicCent = nx.harmonic_centrality(G)
        # res['harmonicCent'] = [harmonicCent[hash] / len(G)
        #                        if hash in harmonicCent else 0 for hash in vul_hash]

        # degreeCent = nx.degree_centrality(G)
        # res['degreeCent'] = [degreeCent[hash]
        #                      if hash in degreeCent else 0 for hash in vul_hash]

        # closenessCent = nx.closeness_centrality(G)
        # res['closenessCent'] = [closenessCent[hash]
        #                         if hash in closenessCent else 0 for hash in vul_hash]

        # betweennessCent = nx.betweenness_centrality(G)
        # res['betweennessCent'] = [betweennessCent[hash]
        #                           if hash in betweennessCent else 0 for hash in vul_hash]
        res['harmonicCent'] = nx.harmonic_centrality(G)
        res['degreeCent'] = nx.degree_centrality(G)
        res['closenessCent'] = nx.closeness_centrality(G)
        res['betweennessCent'] = nx.betweenness_centrality(G)
        return res

    def process_dir(self, path, output_path, language='cpp'):
        if not os.path.exists(path):
            raise Exception('path not exists')

        cwd_dir = os.getcwd()+"/slice"
        code_dir = cwd_dir+"/raw/test"

        shutil.rmtree(os.path.join(cwd_dir, "graph_db", "test"))
        os.mkdir(os.path.join(cwd_dir, "graph_db", "test"))
        shutil.rmtree(os.path.join(cwd_dir, "intermediate"))
        os.mkdir(os.path.join(cwd_dir, "intermediate"))

        dir = os.listdir(path)

        for file in dir:
            # print(os.path.join(path, file))
            os.mkdir(os.path.join(code_dir, file+"."+language))
            shutil.copy2(os.path.join(path, file),
                         os.path.join(code_dir, file+"."+language, file+"."+language))

        pdg_edges = generate_pdg(self.joern_client)

        res = {}
        for file, slice in pdg_edges.items():
            code_map = self.normalize(os.path.join(
                code_dir, file, file))
            hash = self.get_hash(code_map)
            cent = self.get_centrality(slice, hash, set(hash.values()))
            res[file] = cent
            shutil.rmtree(os.path.join(code_dir, file))

        with open(output_path, "wb") as f:
            pickle.dump(res, f)


if __name__ == "__main__":
    parser = SignatureParser('/usr/lib/llvm-10/lib/libclang-10.so.1')

    # f = open("test.c", "r")
    # slice = parser.get_slice(f.read())
    # print(slice)
    # code_map = parser.normalize("test.c")
    # code_hash = parser.get_hash(code_map)
    # for lineNumber, hash in code_hash.items():
    #     print(lineNumber, ": ", hash)
    # res = parser.get_centrality(
    #     slice['code.cpp'], code_hash, set(code_hash.values()))
    # print(res)
