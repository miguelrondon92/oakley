#!/usr/bin/env python3
"""Fix Oakley editable install on macOS (Python 3.12 skips hidden .pth files)."""

from __future__ import annotations

import glob
import os
import site
import subprocess
import sys
from pathlib import Path

BOOTSTRAP_MARKER = "_oakley_bootstrap_src_path"


def _project_src_from_oakley_script(script: Path) -> Path | None:
    # .venv/bin/oakley -> repo root is three levels up in dev layout
    root = script.resolve().parent.parent.parent
    src = root / "src"
    return src if src.is_dir() and (src / "oakley" / "cli.py").exists() else None


def patch_oakley_console_script() -> bool:
    """Prepend src/ to sys.path in the oakley console script (dev editable layout)."""
    script = Path(sys.prefix) / "bin" / "oakley"
    if not script.exists():
        return False

    text = script.read_text(encoding="utf-8")
    if BOOTSTRAP_MARKER in text:
        return False

    src = _project_src_from_oakley_script(script)
    if src is None:
        return False

    bootstrap = f"""
# {BOOTSTRAP_MARKER}
from pathlib import Path as _Path
_oakley_src = _Path({str(src)!r})
if _oakley_src.is_dir() and str(_oakley_src) not in sys.path:
    sys.path.insert(0, str(_oakley_src))
"""
    lines = text.splitlines()
    out: list[str] = []
    inserted = False
    for line in lines:
        out.append(line)
        if not inserted and line.strip() == "import sys":
            out.append(bootstrap.rstrip())
            inserted = True

    if not inserted:
        out = [lines[0], "import sys", bootstrap.rstrip(), *lines[1:]]

    script.write_text("\n".join(out) + "\n", encoding="utf-8")
    return True


def unhide_pth_files(site_packages: str) -> int:
    if sys.platform != "darwin":
        return 0
    count = 0
    for path in glob.glob(os.path.join(site_packages, "*.pth")):
        subprocess.run(["chflags", "nohidden", path], check=False)
        count += 1
    return count


def verify_import() -> bool:
    try:
        import oakley  # noqa: F401

        return True
    except ModuleNotFoundError:
        return False


def main() -> int:
    site_packages = site.getsitepackages()[0]
    n_pth = unhide_pth_files(site_packages)
    patched = patch_oakley_console_script()

    if verify_import():
        parts = []
        if n_pth:
            parts.append(f"unhid {n_pth} .pth file(s)")
        if patched:
            parts.append("patched oakley console script")
        print(f"OK: {'; '.join(parts) or 'editable install already healthy'}")
        return 0

    print(
        "Error: still cannot import oakley. Try:\n"
        "  pip install -e \".[dev]\"\n"
        "  python scripts/fix_venv.py",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
