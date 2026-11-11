# Changelog

What changed in hash-lite, newest first.

## 1.0.0 - 2026-11-10

- First release.
- Hashes text (as UTF-8) or local file bytes with SHA-256, SHA-1, MD5 and optional SHA-512. Hex and Base64 are included by default.
- `--algorithms` picks which hashes to compute. `--no-base64` turns off the Base64 forms.
- `--json` gives one clean object for scripts and AI agents. `--quiet` hides the tip line.
- A free MCP server with two read-only tools: `hash_text` and `hash_file`.
- Needs Python 3.10 or newer.
