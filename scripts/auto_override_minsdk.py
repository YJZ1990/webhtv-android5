#!/usr/bin/env python3
"""Collect every dependency AAR package name and write them into the manifest's
tools:overrideLibrary so the API 21 build never fails on a library minSdk check.

Usage: python3 scripts/auto_override_minsdk.py <manifest path> [extra search roots...]
"""
import glob
import re
import sys
import zipfile
from pathlib import Path

manifest = Path(sys.argv[1])
roots = sys.argv[2:] or [".", str(Path.home() / ".gradle/caches")]

packages = set()


def extract_package(data: bytes):
    for enc in ("utf-8", "utf-16-le"):
        text = data.decode(enc, "ignore")
        m = re.search(r'package[="\s:]{1,12}([a-z][a-z0-9._]+)', text)
        if m:
            return m.group(1)
    return None


for root in roots:
    for aar in glob.glob(str(Path(root) / "**" / "*.aar"), recursive=True):
        try:
            with zipfile.ZipFile(aar) as z:
                if "AndroidManifest.xml" not in z.namelist():
                    continue
                pkg = extract_package(z.read("AndroidManifest.xml"))
                if pkg:
                    packages.add(pkg)
        except Exception:
            continue

# Known transitive packages whose AAR may not be cached locally at scan time.
packages.update({
    "androidx.savedstate", "androidx.savedstate.ktx",
    "androidx.lifecycle.viewmodel.savedstate", "androidx.lifecycle.viewmodel",
    "androidx.lifecycle.runtime", "androidx.lifecycle.process",
    "androidx.activity", "androidx.fragment",
    "androidx.navigation", "androidx.navigation.fragment", "androidx.navigation.ui",
    "androidx.media3.ui.danmaku", "io.github.anilbeesetti.nextlib.media3ext",
    "com.suyashbelekar.exoplayerhdrutils", "com.google.android.material",
    "androidx.work", "androidx.work.ktx", "androidx.work.runtime.ktx",
    "androidx.biometric", "androidx.media", "androidx.preference",
    "androidx.palette", "androidx.recyclerview", "androidx.core",
    "androidx.core.ktx", "androidx.annotation", "androidx.appcompat",
    "androidx.leanback", "androidx.room", "androidx.room.ktx",
    "androidx.startup", "androidx.swiperefreshlayout", "androidx.viewpager2",
    "androidx.webkit", "androidx.drawerlayout", "androidx.constraintlayout",
    "androidx.coordinatorlayout", "androidx.dynamicanimation",
    "androidx.transition", "androidx.vectordrawable",
})

text = manifest.read_text(encoding="utf-8")
joined = ",".join(sorted(packages))
new_tag = f'<uses-sdk tools:overrideLibrary="{joined}" />'
text2 = re.sub(r'<uses-sdk\s+tools:overrideLibrary="[^"]*"\s*/>', new_tag, text)
if text2 == text:
    # no existing tag: insert right after the manifest opening tag
    text2 = re.sub(r'(<manifest[^>]*>)', r'\1\n    ' + new_tag, text, count=1)
manifest.write_text(text2, encoding="utf-8")
print(f"[auto_override] wrote {len(packages)} packages into {manifest}")
print("[auto_override] " + joined)
