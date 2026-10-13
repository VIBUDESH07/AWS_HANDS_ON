#!/usr/bin/env python3
"""docs/chapters/*.md → docs/build/guide.html → PDF (Google Chrome headless).

Setup:  pip install markdown pygments pymdown-extensions
Run:    python3 docs/build_pdf.py
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import markdown
from pygments.formatters import HtmlFormatter

DOCS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = DOCS_DIR.parent
BUILD_DIR = DOCS_DIR / "build"
OUTPUT_PDF = PROJECT_DIR.parent / "Docker-Kubernetes-Fullstack-Tanglish.pdf"

# `<!-- include: k8s/django/deployment.yaml -->` → andha file-oda content code block-a varum.
# Code maarinaalum PDF eppovume project files-oda sync-la irukkum.
INCLUDE_PATTERN = re.compile(r"^<!--\s*include:\s*(\S+)\s*-->$", re.MULTILINE)
LANGUAGE_BY_NAME = {"Dockerfile": "docker", "Makefile": "make"}
LANGUAGE_BY_SUFFIX = {
    ".py": "python",
    ".cs": "csharp",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".js": "javascript",
    ".html": "html",
    ".css": "css",
    ".csproj": "xml",
    ".template": "nginx",
    ".sql": "sql",
}
CHAPTER_HEADING = re.compile(r"<h1([^>]*)>(.*?)</h1>")
HEADING_ID = re.compile(r'id="([^"]+)"')
CHROME_CANDIDATES = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser"]


def include_project_file(match):
    relative_path = match.group(1)
    path = PROJECT_DIR / relative_path
    language = LANGUAGE_BY_NAME.get(path.name) or LANGUAGE_BY_SUFFIX.get(path.suffix, "text")
    content = path.read_text(encoding="utf-8").rstrip()
    return f'<p class="filename">📄 {relative_path}</p>\n\n```{language}\n{content}\n```'


def load_chapters():
    chapter_files = sorted((DOCS_DIR / "chapters").glob("*.md"))
    if not chapter_files:
        sys.exit("docs/chapters-la .md files illa")
    sources = [INCLUDE_PATTERN.sub(include_project_file, path.read_text(encoding="utf-8")) for path in chapter_files]
    return "\n\n".join(sources)


def build_table_of_contents(body_html):
    items = []
    for attributes, title in CHAPTER_HEADING.findall(body_html):
        anchor_match = HEADING_ID.search(attributes)
        if not anchor_match:
            continue
        anchor = anchor_match.group(1)
        if 'class="part"' in attributes:
            items.append(f'<li class="toc-part"><a href="#{anchor}">{title}</a></li>')
        else:
            items.append(f'<li><a href="#{anchor}">{title}</a></li>')
    return '<nav class="toc"><h1 class="toc-title">Contents</h1><ol>' + "".join(items) + "</ol></nav>"


def render_html():
    converter = markdown.Markdown(
        # superfences: admonition / list ulla irukka code blocks-um correct-a parse aagum
        extensions=[
            "pymdownx.highlight",
            "pymdownx.superfences",
            "tables",
            "toc",
            "admonition",
            "attr_list",
            "md_in_html",
            "sane_lists",
        ],
        extension_configs={"pymdownx.highlight": {"guess_lang": False, "css_class": "highlight"}},
    )
    body_html = converter.convert(load_chapters())
    template = (DOCS_DIR / "template.html").read_text(encoding="utf-8")
    pygments_css = HtmlFormatter(style="friendly").get_style_defs(".highlight")
    return (
        template.replace("{{pygments_css}}", pygments_css)
        .replace("{{toc}}", build_table_of_contents(body_html))
        .replace("{{body}}", body_html)
    )


def find_chrome():
    for name in CHROME_CANDIDATES:
        path = shutil.which(name)
        if path:
            return path
    sys.exit("Chrome/Chromium kidaikkala — PDF render panna adhu venum")


def main():
    BUILD_DIR.mkdir(exist_ok=True)
    html_path = BUILD_DIR / "guide.html"
    html_path.write_text(render_html(), encoding="utf-8")
    print(f"HTML  → {html_path}")

    subprocess.run(
        [
            find_chrome(),
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            "--generate-pdf-document-outline",
            f"--print-to-pdf={OUTPUT_PDF}",
            html_path.as_uri(),
        ],
        check=True,
        stderr=subprocess.DEVNULL,
    )
    print(f"PDF   → {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
