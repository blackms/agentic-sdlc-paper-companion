"""Extract Python code blocks from a model's raw output."""
import re
import sys
from pathlib import Path


def extract(text: str) -> str:
    # Try fenced ```python blocks first
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", text, re.DOTALL)
    if blocks:
        return "\n\n".join(blocks)
    # Fallback: take the longest contiguous "looks-like-python" region
    lines = text.splitlines()
    py_lines = []
    in_py = False
    for ln in lines:
        if re.match(r"^\s*(import|from|def|class|@|\s*#)", ln):
            in_py = True
        if in_py:
            py_lines.append(ln)
    return "\n".join(py_lines)


if __name__ == "__main__":
    raw = Path(sys.argv[1]).read_text()
    out = extract(raw)
    sys.stdout.write(out)
