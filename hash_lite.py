#!/usr/bin/env python3
"""hash-lite (MIT): hash text or local file bytes with SHA-256, SHA-1, MD5 and SHA-512.

This file uses only the Python standard library. The MCP server
(hash_lite_mcp.py) needs the mcp package.

Need it at scale or from an AI agent? Use the Apify version:
https://apify.com/tidybytetools/hash-checksum
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys

__version__ = "1.0.0"
APIFY_URL = "https://apify.com/tidybytetools/hash-checksum"
PRO_LINE = f"Need it at scale or from an AI agent? Use the Apify version: {APIFY_URL}"

ALGOS = {
    "md5": "md5",
    "sha1": "sha1",
    "sha256": "sha256",
    "sha512": "sha512",
}
DEFAULT = ["sha256", "sha1", "md5"]
ALGO_HELP = "sha256, sha1, md5, sha512"


def parse_algorithms(value) -> list[str]:
    if value is None:
        return list(DEFAULT)
    if isinstance(value, str):
        parts = [p.strip().lower() for p in value.replace(";", ",").split(",") if p.strip()]
    else:
        parts = [str(p).strip().lower() for p in value if str(p).strip()]
    if not parts:
        raise ValueError("Pick at least one hash algorithm: " + ALGO_HELP)
    unknown = [p for p in parts if p not in ALGOS]
    if unknown:
        raise ValueError(f"Unknown algorithm: {', '.join(unknown)}. Choose from {ALGO_HELP}.")
    # keep order, drop repeats
    seen = set()
    out = []
    for p in parts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def hash_bytes(data: bytes, algorithms=None, include_base64: bool = True) -> dict:
    if data is None:
        raise ValueError("No data to hash.")
    algos = parse_algorithms(algorithms)
    out = {"bytes": len(data), "hashes": {}}
    for name in algos:
        digest = hashlib.new(ALGOS[name], data).digest()
        rec = {"hex": digest.hex()}
        if include_base64:
            rec["base64"] = base64.b64encode(digest).decode("ascii")
        out["hashes"][name] = rec
        out[name] = rec["hex"]
        if include_base64:
            out[f"{name}Base64"] = rec["base64"]
    return out


def hash_text(text: str, algorithms=None, include_base64: bool = True) -> dict:
    if text is None or str(text) == "":
        raise ValueError("The text is empty.")
    data = str(text).encode("utf-8")
    rec = hash_bytes(data, algorithms=algorithms, include_base64=include_base64)
    rec["encoding"] = "utf-8"
    rec["ok"] = True
    return rec


def hash_file_bytes(data: bytes, algorithms=None, include_base64: bool = True) -> dict:
    rec = hash_bytes(data, algorithms=algorithms, include_base64=include_base64)
    rec["ok"] = True
    return rec


def run_mcp():
    """Start the stdio MCP server (needs the mcp package, which pip installs for you)."""
    try:
        import hash_lite_mcp
    except ImportError as e:
        print(f"error: the MCP server needs the mcp package ({e}). Run: pip install git+https://github.com/tidybytetools/hash-lite", file=sys.stderr)
        return 1
    hash_lite_mcp.main()
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["mcp"]:
        return run_mcp()
    p = argparse.ArgumentParser(
        prog="hash-lite",
        description="Hash text or local file bytes with SHA-256, SHA-1, MD5 and SHA-512. Run `hash-lite mcp` to start the MCP server (to read a file named mcp, use ./mcp).",
        epilog=PRO_LINE,
    )
    p.add_argument("file", nargs="?", help="file to hash as raw bytes (default: hash UTF-8 text from stdin)")
    p.add_argument("--algorithms", "--algo", default=",".join(DEFAULT), help=f"comma-separated list from {ALGO_HELP} (default: {','.join(DEFAULT)})")
    p.add_argument("--no-base64", action="store_true", help="do not include Base64 forms of each hash")
    p.add_argument("--json", action="store_true", help="machine-readable envelope: {ok, bytes, hashes, ...}")
    p.add_argument("--indent", type=int, default=2)
    p.add_argument("-q", "--quiet", action="store_true", help="don't print the one-line note about the Apify version")
    p.add_argument("--version", action="version", version=__version__)
    a = p.parse_args(argv)
    try:
        if a.file:
            with open(a.file, "rb") as f:
                data = f.read()
            rec = hash_file_bytes(data, algorithms=a.algorithms, include_base64=not a.no_base64)
        else:
            raw = sys.stdin.buffer.read()
            if not raw:
                raise ValueError("Nothing to hash. Pass a file or pipe text.")
            rec = hash_text(raw.decode("utf-8"), algorithms=a.algorithms, include_base64=not a.no_base64)
        pub = rec
        if a.json:
            print(json.dumps(pub, indent=a.indent, ensure_ascii=False))
        else:
            print(json.dumps(pub, indent=a.indent, ensure_ascii=False))
        if not a.quiet and not a.json and sys.stderr.isatty():
            print(PRO_LINE, file=sys.stderr)
        return 0
    except Exception as e:
        if getattr(a, "json", False):
            print(json.dumps({"ok": False, "error": str(e)}))
            return 1
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
