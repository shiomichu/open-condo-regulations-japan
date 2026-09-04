#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import difflib
import re
import sys
from pathlib import Path

from pypdf import PdfReader

# ============================================================
# Patterns
# ============================================================

ARTICLE_RE = re.compile(
    r"(第\s*[0-9０-９]+条(?:の\s*[0-9０-９]+)?)"
)

IF_RE = re.compile(
    r"<!--\s*IF\s+([A-Z0-9_]+)\s*-->"
)

ENDIF_RE = re.compile(
    r"<!--\s*ENDIF\s*-->"
)

# ============================================================
# PDF
# ============================================================


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


# ============================================================
# Normalize
# ============================================================


def normalize(text: str) -> str:

    # IFコメント除去
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
        flags=re.MULTILINE,
    )

    text = text.replace("**", "")

    trans = str.maketrans(
        "０１２３４５６７８９",
        "0123456789"
    )

    text = text.translate(trans)

    text = text.replace("　", " ")

    text = re.sub(r"\r\n", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


# ============================================================
# Split Articles
# ============================================================


def split_articles(text: str):

    text = normalize(text)

    result = {}

    matches = list(
        ARTICLE_RE.finditer(text)
    )

    for i, match in enumerate(matches):

        article = re.sub(
            r"\s+",
            "",
            match.group(1)
        )

        start = match.start()

        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)

        body = text[start:end].strip()

        result[article] = body

    return result


# ============================================================
# Similarity
# ============================================================


def similarity(a, b):

    return difflib.SequenceMatcher(
        None,
        a,
        b
    ).ratio()


def make_diff(a, b):

    return "\n".join(
        difflib.unified_diff(
            a.splitlines(),
            b.splitlines(),
            fromfile="PDF",
            tofile="Markdown",
            lineterm=""
        )
    )


# ============================================================
# config.env
# ============================================================


def load_env_flags(env_path: Path):

    flags = {}

    if not env_path.exists():
        return flags

    for line in env_path.read_text(
        encoding="utf-8"
    ).splitlines():

        line = line.strip()

        if not line:
            continue

        if line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, value = line.split(
            "=",
            1
        )

        flags[key.strip()] = value.strip()

    return flags


# ============================================================
# IF validator
# ============================================================


def check_if_blocks(
    markdown_text,
    valid_flags
):

    warnings =
