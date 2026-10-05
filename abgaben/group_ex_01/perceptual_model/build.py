"""Render the perceptual model as a vector A4 PDF (Graphviz + LaTeX) and a PNG preview."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from perceptual_model.layout import node_anchor  # noqa: E402

FIGURES = HERE.parent / "figures"
DOT = "/opt/homebrew/bin/dot"
PDFLATEX = "/Library/TeX/texbin/pdflatex"
PDFTOPPM = "/opt/homebrew/bin/pdftoppm"


def graphviz(fmt: str, out: Path | None = None) -> str:
    args = [DOT, f"-T{fmt}", str(HERE / "perceptual_model.dot")]
    if out is not None:
        args += ["-o", str(out)]
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        graphviz("pdf", work / "diagram.pdf")
        anchor = node_anchor(graphviz("plain"), "eq")
        (work / "anchor.tex").write_text(
            f"\\newcommand\\EqX{{{anchor.x:.5f}}}\n"
            f"\\newcommand\\EqY{{{anchor.y:.5f}}}\n"
            f"\\newcommand\\EqWidth{{{anchor.width:.5f}}}\n"
        )
        subprocess.run(
            [PDFLATEX, "-interaction=nonstopmode", "-halt-on-error", str(HERE / "a4_page.tex")],
            cwd=work,
            check=True,
            stdout=subprocess.DEVNULL,
        )
        out = FIGURES / "perceptual_model.pdf"
        shutil.copyfile(work / "a4_page.pdf", out)
    subprocess.run(
        [PDFTOPPM, "-png", "-r", "200", "-singlefile", str(out), str(FIGURES / "perceptual_model")],
        check=True,
    )


if __name__ == "__main__":
    main()
