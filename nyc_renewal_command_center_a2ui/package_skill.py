#!/usr/bin/env python3
"""Standalone Python 3 stdlib CLI embedder & .zip packager for `nyc_renewal_a2ui_skill`."""

from __future__ import annotations

import base64
import gzip
import pathlib
import re
import zipfile

MARKER = "NYC_RENEWAL_A2UI_CLI_B64:"


def main() -> int:
    root = pathlib.Path(__file__).resolve().parent
    skill_dir = root / "nyc_renewal_a2ui_skill"
    cli_path = skill_dir / "scripts" / "nyc_renewal_a2ui_cli.py"
    md_path = skill_dir / "SKILL.md"
    zip_path = root / "nyc_renewal_a2ui_skill.zip"

    cli_bytes = cli_path.read_bytes()
    b64 = base64.b64encode(gzip.compress(cli_bytes, compresslevel=9)).decode("ascii")
    md_text = md_path.read_text(encoding="utf-8")

    pattern = rf"{re.escape(MARKER)}[A-Za-z0-9+/=]+"
    if re.search(pattern, md_text):
        updated_md = re.sub(pattern, f"{MARKER}{b64}", md_text, count=1)
    else:
        updated_md = (
            md_text.rstrip()
            + f"\n\n## Embedded Helper CLI Payload (`nyc_renewal_a2ui_cli.py`)\n\n```text\n{MARKER}{b64}\n```\n"
        )

    md_path.write_text(updated_md, encoding="utf-8")
    m = re.search(rf"{re.escape(MARKER)}([A-Za-z0-9+/=]+)", md_path.read_text(encoding="utf-8"))
    assert m and gzip.decompress(base64.b64decode(m.group(1))) == cli_bytes, "Roundtrip verification failed"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(md_path, "SKILL.md")
        zf.write(cli_path, "scripts/nyc_renewal_a2ui_cli.py")

    print(f"Packaged {zip_path} ({zip_path.stat().st_size} bytes) successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
