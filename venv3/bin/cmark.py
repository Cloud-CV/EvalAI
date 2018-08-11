#!/Users/dhruv/Documents/gsoc/EvalAI/venv3/bin/python3
import argparse, sys
import CommonMark
parser = argparse.ArgumentParser(description="Process Markdown according to the CommonMark specification.")
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf-8')
parser.add_argument('infile', nargs="?", type=argparse.FileType('r'), default=sys.stdin, help="Input Markdown file to parse, defaults to STDIN")
parser.add_argument('-o', nargs="?", type=argparse.FileType('w'), default=sys.stdout, help="Output HTML/JSON file, defaults to STDOUT")
parser.add_argument('-a', action="store_true", help="Print formatted AST")
parser.add_argument('-aj', action="store_true", help="Output JSON AST")
args = parser.parse_args()
parser = CommonMark.DocParser()
f = args.infile
o = args.o
lines = []
for line in f:
    lines.append(line)
data = "".join(lines)
ast = parser.parse(data)
if not args.a and not args.aj:
    renderer = CommonMark.HTMLRenderer()
    o.write(renderer.render(ast))
    exit()
if args.a:
    # print ast
    CommonMark.dumpAST(ast)
    exit()

#o.write(ast.to_JSON())
o.write(CommonMark.ASTtoJSON(ast))
exit()
