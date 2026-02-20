import ast
import os
import sys

root = r"d:\Coding\Personal_Projects\FinRAG\backend\app"
errors = []
count = 0

for dirpath, dirnames, filenames in os.walk(root):
    for f in filenames:
        if f.endswith(".py"):
            fpath = os.path.join(dirpath, f)
            count += 1
            try:
                with open(fpath, encoding="utf-8") as fh:
                    ast.parse(fh.read())
            except SyntaxError as e:
                errors.append(f"SYNTAX ERROR in {fpath}: {e}")

if errors:
    for e in errors:
        print(e)
    sys.exit(1)
else:
    print(f"All {count} Python files parsed successfully — no syntax errors.")
