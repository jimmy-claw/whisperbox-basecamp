#!/usr/bin/env python3
"""Generate the Basecamp catalog index.json (schemaVersion 2) from a set of
.lgx files, emitting PUBLIC GitHub release-download URLs.

    gen-index.py <owner/repo> <tag> <file1.lgx> [file2.lgx ...]

For each .lgx it reads the embedded manifest.json, computes sha256 + size, and
sets rootHash from manifest.hashes.root. The `url` points at the stable release
asset:

    https://github.com/<owner>/<repo>/releases/download/<tag>/<basename>.lgx

so Basecamp can download it from anywhere, not just a LAN.
(Adapted from vpavlin/kym-basecamp.)
"""
import glob
import hashlib
import json
import subprocess
import sys
import datetime

if len(sys.argv) < 4:
    sys.exit(__doc__)

repo = sys.argv[1]          # owner/repo
tag = sys.argv[2]
lgx_args = sys.argv[3:]

# expand globs / dirs so callers can pass "dist/*.lgx" or a directory
files = []
for a in lgx_args:
    if a.endswith(".lgx"):
        files.extend(sorted(glob.glob(a)) or [a])
    else:  # treat as a directory
        files.extend(sorted(glob.glob(f"{a.rstrip('/')}/*.lgx")))
files = sorted(dict.fromkeys(files))  # unique, stable order

now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
packages = []
for lgx in files:
    try:
        m = json.loads(subprocess.check_output(["tar", "xzOf", lgx, "manifest.json"]))
    except Exception as e:
        print(f"skip {lgx}: {e}", file=sys.stderr)
        continue
    data = open(lgx, "rb").read()
    base = lgx.split("/")[-1]
    packages.append({
        "name": m["name"],
        "versions": [{
            "releasedAt": now,
            "publisherRef": f"{m['name']}-v{m.get('version', '0.0.0')}",
            "url": f"https://github.com/{repo}/releases/download/{tag}/{base}",
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "rootHash": m["hashes"]["root"],
            "manifest": m,
        }],
    })

# stable package order (delivery_module, whisperbox, whisperbox_core ...)
packages.sort(key=lambda p: p["name"])

json.dump({
    "schemaVersion": 2,
    "repositoryName": repo.split("/")[-1],
    "generatedAt": now,
    "packages": packages,
}, sys.stdout, indent=2)
print()
