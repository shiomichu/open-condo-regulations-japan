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

# テンプレート Markdown を読み込む
with open("template.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

output = []

# 条件のスタック（True = 出力する、False = 出力しない）
condition_stack = []

for line in lines:
    # IF ブロック開始
    m = re.match(r"<!-- IF ([A-Z0-9_]+) -->", line)
    if m:
        key = m.group(1)
        # このブロックを出力するか？
        current = env.get(key, False)
        condition_stack.append(current)
        continue

    # ENDIF
    if re.match(r"<!-- ENDIF -->", line):
        if condition_stack:
            condition_stack.pop()
        continue

    # 現在の状態：スタックに False があれば出力しない
    if False not in condition_stack:
        output.append(line)

# 出力
with open("dist/output.md", "w", encoding="utf-8") as f:
    f.writelines(output)
