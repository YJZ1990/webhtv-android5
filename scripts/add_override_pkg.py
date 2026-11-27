#!/usr/bin/env python3
"""Append one package name to the manifest's tools:overrideLibrary attribute."""
import re
import sys
from pathlib import Path

manifest = Path(sys.argv[1])
pkg = sys.argv[2].strip()
if not pkg:
    sys.exit(0)

text = manifest.read_text(encoding="utf-8")


def repl(m):
    existing = [p for p in m.group(1).split(",") if p]
    if pkg in existing:
        return m.group(0)
    existing.append(pkg)
    return '<uses-sdk tools:overrideLibrary="%s" />' % ",".join(existing)


new = re.sub(r'<uses-sdk\s+tools:overrideLibrary="([^"]*)"\s*/>', repl, text)
manifest.write_text(new, encoding="utf-8")
print(f"[add_override] added {pkg}")
