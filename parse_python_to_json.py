'''

Parses a Python source file into an AST in JSON format. can be viewed
online in a viewer like: http://jsonviewer.stack.hu/

Usage:

python parse_python_to_json.py --pyfile=test.py      # pass in code within a file
python parse_python_to_json.py 'print "Hello world"' # pass in code as a string

Try running on its own source code; whoa very META!

python parse_python_to_json.py --pyfile=parse_python_to_json.py


Output: prints JSON to stdout

Created on 2017-01-20 by Philip Guo
'''
import fnmatch
import json
import optparse
import os
import re
import sys

# import pprint
import pythonparser  # based on https://github.com/m-labs/pythonparser


def parse_directory(code, indent_level=None):
    print("parse")

    try:
        p = pythonparser.parse(code)

        v = Visitor()
        res = v.visit(p)
        # print(json.dumps(res, indent=indent_level))
        module = json.dumps(res, indent=indent_level)

    except pythonparser.diagnostic.Error as e:
        error_obj = {'type': 'parse_error'}
        diag = e.diagnostic
        loc = diag.location

        error_obj['loc'] = {
            'start': {'line': loc.begin().line(), 'column': loc.begin().column()},
            'end': {'line': loc.end().line(), 'column': loc.end().column()}
        }

        error_obj['message'] = diag.message()
        print(json.dumps(error_obj, indent=indent_level))
        sys.exit(1)

    return module


# pp = pprint.PrettyPrinter()

class Visitor:
    def visit(self, obj, level=0):
        """Visit a node or a list of nodes. Other values are ignored"""
        if isinstance(obj, list):
            return [self.visit(elt, level) for elt in obj]

        elif isinstance(obj, pythonparser.ast.AST):
            typ = obj.__class__.__name__
            # print >> sys.stderr, obj
            loc = None
            if hasattr(obj, 'loc'):
                loc = {
                    'start': {'line': obj.loc.begin().line(), 'column': obj.loc.begin().column()},
                    'end': {'line': obj.loc.end().line(), 'column': obj.loc.end().column()}
                }
            # TODO: check out obj._locs for more details later if needed

            d = {}
            d['type'] = typ
            d['loc'] = loc
            d['_fields'] = obj._fields
            for field_name in obj._fields:
                val = self.visit(getattr(obj, field_name), level + 1)
                d[field_name] = val
            return d

        else:
            # let's hope this is a primitive type that's JSON-encodable!
            return obj


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("--pydirectory", action="store", dest="pydirectory",
                      help="Take input from a Directory with Python files")
    parser.add_option("--pyfile", action="store", dest="pyfile",
                      help="Take input from a Python source file")
    parser.add_option("--pp", action="store_true",
                      help="Pretty-print JSON for human viewing")
    (options, args) = parser.parse_args()

    output_modules = []

    if options.pydirectory:
        includes = ['*.py']  # for files only
        excludes = ['/home/tiago/Documents/Pessoal/Tese/Honeycomb/python-parse-to-json/.git',
                    '/home/tiago/Documents/Pessoal/Tese/Honeycomb/python-parse-to-python/.idea/']  # for dirs and files

        # transform glob patterns to regular expressions
        includes = r'|'.join([fnmatch.translate(x) for x in includes])
        excludes = r'|'.join([fnmatch.translate(x) for x in excludes]) or r'$.'

        for root, dirs, files in os.walk('Samples'):

            # exclude dirs
            dirs[:] = [os.path.join(root, d) for d in dirs]
            dirs[:] = [d for d in dirs if not re.match(excludes, d)]

            # exclude/include files
            files = [os.path.join(root, f) for f in files]
            files = [f for f in files if not re.match(excludes, f)]
            files = [f for f in files if re.match(includes, f)]

            for file in files:
                print(file)
                print("Opening...")
                code = open(file).read()
                print("Preparing to parse")
                output_modules.append(
                    {
                        "name": file,
                        "data": parse_directory(code)
                    })
                print(".")

    if options.pyfile:
        indent_level = None
        if options.pp:
            indent_level = 2
        print(options.pyfile, indent_level)
        code = open(options.pyfile).read()
        output_modules.append(parse_directory(code))
    # else:
    #     code = #args[0]
    #     # make sure it ends with a newline to get parse() to work:
    #     if code[-1] != '\n':
    #         code += '\n'
    #     output_modules.append(parse_directory(code))
    json_data = []
    i = 0
    for module in output_modules:
        print(module)
        json_data.append({
            "index": i,
            "module": module
        })
        i += 1
        # pass
    print("Dumping")
    with open('data.json', 'w') as fp:
        json.dump(json_data, fp, sort_keys=True, indent=4)
    print("Existing")
    sys.exit(1)
