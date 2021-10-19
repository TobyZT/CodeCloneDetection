from anytree import AnyNode
from pycparser import c_parser, c_ast, c_generator

text = r"""
int max(int x,int y)
{
    int t;
    t = x>y?x:y;
    return t;
}

int main()
{
    int maxs;
    maxs = max(2,3);
    printf("%d",maxs);
}
"""


def create(node, root, nodelist, _my_node_name=None, parent=None):
    id = len(nodelist)

    if _my_node_name is not None:
        token = node.__class__.__name__  # + ' <' + _my_node_name + '>: '
    else:
        token = node.__class__.__name__  # + ': '

    if id == 0:
        root.token = token
        root.data = node
    else:
        newnode = AnyNode(id=id, token=token, data=node, parent=parent)
    nodelist.append(node)

    for (child_name, child) in node.children():
        if id == 0:
            create(child, root, nodelist, _my_node_name=child_name, parent=root)
        else:
            create(child, root, nodelist, _my_node_name=child_name, parent=newnode)


def traverse(root, nodelist):
    if len(root.children()) == 0:
        return
    for (_, child) in root.children():
        nodelist.append(child.__class__.__name__)
        if len(child.children()) == 0:
            pass
        traverse(child, nodelist)


def mycreate(ast):
    nodelist = []
    traverse(ast, nodelist)
    return nodelist


if __name__ == '__main__':
    parser = c_parser.CParser()
    ast = parser.parse(text)
    nodelist = mycreate(ast)
    print(nodelist)
