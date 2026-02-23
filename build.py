import sys
import re

env_file = sys.argv[1]

# env を読み込む
env = {}
with open(env_file, "r", encoding="utf-8") as f:
    for line in f:
        if "=" in line:
            key, value = line.strip().split("=", 1)
            env[key] = value.lower() in ("1", "true", "yes", "on")


import glob

output = []

def append_md_with_pagebreak(md_path):
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    condition_stack = []
    for line in lines:
        # IF ブロック開始
        m = re.match(r"<!-- IF ([A-Z0-9_]+) -->", line)
        if m:
            key = m.group(1)
            current = env.get(key, False)
            condition_stack.append(current)
            continue
        # ENDIF
        if re.match(r"<!-- ENDIF -->", line):
            if condition_stack:
                condition_stack.pop()
            continue
        if False not in condition_stack:
            # セクションタイトル（#で始まる行）の前にページ区切りを挿入
            if re.match(r"^# ", line):
                output.append('<div style="page-break-before:always"></div>\n')
            output.append(line)

# 本文
append_md_with_pagebreak("01_標準管理規約/01_本文/管理規約.md")

# 02_別表配下の2桁数字で始まるmd
for path in sorted(glob.glob("01_標準管理規約/02_別表/[0-9][0-9]_*.md")):
    output.append('<div style="page-break-before:always"></div>\n')
    append_md_with_pagebreak(path)

# 03_細則配下の2桁数字で始まるmd
for path in sorted(glob.glob("01_標準管理規約/03_細則/[0-9][0-9]_*.md")):
    output.append('<div style="page-break-before:always"></div>\n')
    append_md_with_pagebreak(path)

# 出力
with open("dist/output.md", "w", encoding="utf-8") as f:
    f.writelines(output)
