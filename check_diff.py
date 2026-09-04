#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
check_diff.py

原本PDFと build.py の生成結果を比較する。

Usage:

python check_diff.py \
  --pdf reference/単棟型管理規約20251017改正.pdf \
  --md build/管理規約.md
"""

import argparse
import difflib
import re
from pathlib import Path

from pypdf import PdfReader


ARTICLE_RE = re.compile(
    r"(第\s*[0-9０-９]+条(?:の\s*[0-9０-９]+)?)"
)


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))

    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""

        # ページ番号除去
        text = re.sub(
            r"\n\s*-\s*\d+\s*-\s*\n",
            "\n",
            text
        )

        pages.append(text)

    return "\n".join(pages)


def normalize(text: str) -> str:

    # IFブロック除去
    text = re.sub(
        r"<!--.*?-->",
        "",
        text,
        flags=re.DOTALL
    )

    # Markdown見出し除去
    text = re.sub(
        r"^#+\s*",
        "",
        text,
        flags=re.MULTILINE
    )

    # 太字
    text = text.replace("**", "")

    # 全角数字→半角
    trans = str.maketrans(
        "０１２３４５６７８９",
        "0123456789"
    )

    text = text.translate(trans)

    # 全角スペース
    text = text.replace("　", " ")

    # 改行整理
    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


def split_articles(text: str):

    text = normalize(text)

    result = {}

    matches = list(
        ARTICLE_RE.finditer(text)
    )

    for i, m in enumerate(matches):

        article = re.sub(
            r"\s+",
            "",
            m.group(1)
        )

        start = m.start()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        body = text[start:end].strip()

        result[article] = body

    return result


def similarity(a: str, b: str) -> float:
    return difflib.SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def make_diff(a: str, b: str) -> str:

    return "\n".join(
        difflib.unified_diff(
            a.splitlines(),
            b.splitlines(),
            fromfile="PDF",
            tofile="Markdown",
            lineterm=""
        )
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--pdf",
        required=True
    )

    parser.add_argument(
        "--md",
        required=True
    )

    parser.add_argument(
        "--report",
        default="reports/diff_report.md"
    )

    args = parser.parse_args()

    print("Loading PDF...")
    pdf_text = extract_pdf_text(
        Path(args.pdf)
    )

    print("Loading Markdown...")
    md_text = Path(args.md).read_text(
        encoding="utf-8"
    )

    pdf_articles = split_articles(pdf_text)
    md_articles = split_articles(md_text)

    report = []
    errors = 0
    warnings = 0
    matches = 0

    all_articles = sorted(
        set(pdf_articles.keys())
        | set(md_articles.keys())
    )

    report.append("# Diff Report\n")

    for article in all_articles:

        pdf_body = pdf_articles.get(article)
        md_body = md_articles.get(article)

        if pdf_body is None:
            errors += 1

            report.append(
                f"## {article}\n"
                "ERROR: PDFに存在しません\n"
            )

            continue

        if md_body is None:
            errors += 1

            report.append(
                f"## {article}\n"
                "ERROR: Markdownに存在しません\n"
            )

            continue

        score = similarity(
            pdf_body,
            md_body
        )

        if score >= 0.995:
            matches += 1
            continue

        if score >= 0.97:

            warnings += 1

            report.append(
                f"## {article}\n\n"
                f"WARNING ({score:.2%})\n\n"
                "```diff\n"
                f"{make_diff(pdf_body, md_body)[:5000]}\n"
                "```\n"
            )

        else:

            errors += 1

            report.append(
                f"## {article}\n\n"
                f"ERROR ({score:.2%})\n\n"
                "```diff\n"
                f"{make_diff(pdf_body, md_body)[:5000]}\n"
                "```\n"
            )

    summary = [
        "# Summary",
        "",
        f"- Match: {matches}",
        f"- Warning: {warnings}",
        f"- Error: {errors}",
        "",
        "---",
        ""
    ]

    output = "\n".join(
        summary + report
    )

    report_path = Path(args.report)

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    report_path.write_text(
        output,
        encoding="utf-8"
    )

    print()
    print(f"Match:   {matches}")
    print(f"Warning: {warnings}")
    print(f"Error:   {errors}")
    print()
    print(f"Report: {report_path}")

    # CI失敗判定
    if errors > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
