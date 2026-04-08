"""Export research report from Markdown to HTML/PDF."""

from __future__ import annotations

from pathlib import Path

from markdown_it import MarkdownIt

_CSS = """\
body {
  font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
  max-width: 800px;
  margin: 2rem auto;
  padding: 0 1rem;
  line-height: 1.7;
  color: #1a1a1a;
}
h1 { border-bottom: 2px solid #2563eb; padding-bottom: 0.5rem; }
h2 { color: #2563eb; margin-top: 2rem; }
blockquote {
  border-left: 4px solid #93c5fd;
  margin-left: 0;
  padding: 0.5rem 1rem;
  background: #eff6ff;
  color: #1e40af;
}
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
code { background: #f1f5f9; padding: 0.2rem 0.4rem; border-radius: 3px; font-size: 0.9em; }
pre { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 6px; overflow-x: auto; }
table { border-collapse: collapse; width: 100%; margin: 1rem 0; }
th, td { border: 1px solid #e2e8f0; padding: 0.5rem; text-align: left; }
th { background: #f8fafc; }
"""


def _md_to_html(md_content: str) -> str:
    md = MarkdownIt("commonmark", {"html": True}).enable("table")
    body = md.render(md_content)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="ru">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<style>{_CSS}</style>\n"
        "</head>\n<body>\n"
        f"{body}\n"
        "</body>\n</html>"
    )


def export_report(artifacts_dir: str, fmt: str = "html") -> str:
    """Export report.md to the given format.

    Args:
        artifacts_dir: Path to the research artifacts directory.
        fmt: Output format — "html" or "pdf".

    Returns:
        Path to the exported file.
    """
    report_path = Path(artifacts_dir) / "report.md"
    if not report_path.exists():
        raise FileNotFoundError(f"Report not found: {report_path}")

    md_content = report_path.read_text(encoding="utf-8")
    export_dir = Path(artifacts_dir) / "export"
    export_dir.mkdir(exist_ok=True)

    if fmt == "html":
        html = _md_to_html(md_content)
        out_path = export_dir / "report.html"
        out_path.write_text(html, encoding="utf-8")
        return str(out_path)

    elif fmt == "pdf":
        try:
            from md2pdf.core import md2pdf as _md2pdf

            out_path = export_dir / "report.pdf"
            _md2pdf(
                str(out_path),
                md_content=md_content,
                css_file_path=None,
            )
            return str(out_path)
        except ImportError:
            html = _md_to_html(md_content)
            out_path = export_dir / "report.html"
            out_path.write_text(html, encoding="utf-8")
            return str(out_path) + " (PDF unavailable — install md2pdf)"

    else:
        raise ValueError(f"Unsupported format: {fmt}. Use 'html' or 'pdf'.")
