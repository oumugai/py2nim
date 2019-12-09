import sys
import ast
import re


def __pass__(arg):
    print(arg)
    return arg

def convert_range(child):
    if len(child) == 1:
        child.insert(0, ast.Num(n=0))
    return child

def convert_input(child):
    if len(child) == 0:
        child.insert(0, ast.Name(id="stdin"))
    print(child)
    return child

table = {
    "function":{
        "print":["echo", __pass__],
        "range":["countup", convert_range],
        "int":["parseInt",  __pass__],
        "input":["readLine", convert_input, "strutils"],
    }
}

import_libs = []

def walk(node, table, indent=0):
    code = []
    flag = True
    if node.__class__ == ast.Call:
        if node.func.id in table["function"]:
            conv_func = table["function"][node.func.id]
            node.func.id = conv_func[0]
            node.args = conv_func[1](node.args)
            if len(conv_func) > 2:
                import_libs.append(conv_func[2])
        args = []
        if hasattr(node, 'args'):
            for arg in node.args:
                if arg.__class__ == ast.Str:
                    args.append('"%s"'%(arg.s))
                elif arg.__class__ == ast.Num:
                    args.append(str(arg.n))
                elif arg.__class__ == ast.Name:
                    args.append(arg.id)
                elif arg.__class__ == ast.Call:
                    args.append(walk(arg, table, indent=indent+1))
        code.append("%s(%s)"%(node.func.id, ", ".join(args)))
        flag = False
    elif node.__class__ == ast.For:
        code.append("for")
        code.append(walk(node.target, table, indent=indent+1))
        code.append("in")
        code.append(walk(node.iter, table, indent=indent+1) + ":\n")
        for child in node.body:
            code.append("  "*(indent) + walk(child, table, indent=indent+1))
        flag = False
    elif node.__class__ == ast.If:
        code.append("if")
        code.append(walk(node.test, table, indent=indent+1) + ":\n")
        for child in node.body:
            code.append("  "*(indent) + walk(child, table, indent=indent+1))
        if len(node.orelse) != 0:
            code.append("  "*(indent-1) + "else:\n")
            for child in node.orelse:
                code.append("  "*(indent) + walk(child, table, indent=indent+1))
        flag = False
    elif node.__class__ == ast.Compare:
        code.append(walk(node.left, table, indent=indent+1))
        for op in node.ops:
            code.append(walk(op, table, indent=indent+1))
        for comp in node.comparators:
            code.append(walk(comp, table, indent=indent+1))
        flag = False
    elif node.__class__ == ast.BinOp:
        code.append("(")
        code.append(walk(node.left, table, indent=indent+1))
        code.append(walk(node.op, table, indent=indent+1))
        code.append(walk(node.right, table, indent=indent+1))
        code.append(")")
        flag = False
    elif node.__class__ == ast.Expr:
        code.append(walk(node.value, table, indent=indent+1))
        code.append("\n")
        flag = False
    elif node.__class__ == ast.Name:
        code.append(node.id)
    elif node.__class__ == ast.Str:
        code.append(node.s)
    elif node.__class__ == ast.Num:
        code.append(str(node.n))
    elif node.__class__ == ast.Add:
        code.append("+")
    elif node.__class__ == ast.Sub:
        code.append("-")
    elif node.__class__ == ast.Mult:
        code.append("*")
    elif node.__class__ == ast.Div:
        code.append("/")
    elif node.__class__ == ast.Mod:
        code.append("mod")
    elif node.__class__ == ast.Eq:
        code.append("==")
    elif node.__class__ == ast.NotEq:
        code.append("!=")
        
    if flag:
        for child in ast.iter_child_nodes(node):
            code.append(walk(child, table, indent=indent+1))
    print(code)
    if indent == 0:
        for libs in import_libs:
            code.insert(0, "import %s"%(libs))
        return "\n".join(code)
    return " ".join(code)

def convert(code, table):
    tree = ast.parse("".join(code), sys.argv[1])
    code = walk(tree, table)
    return code

def main():
    if len(sys.argv) == 2:
        source = []
        with open(sys.argv[1], "r") as file:
            source = file.readlines()
        convert_source = convert(source, table)
        tree = ast.parse("".join(source), sys.argv[1])
        with open(sys.argv[1].replace(".py", ".nim"), "w") as file:
            file.write(convert_source)


if __name__ == "__main__":
    main()