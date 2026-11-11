"""Free MCP server for hash-lite (stdio).

Run:  uvx --from git+https://github.com/tidybytetools/hash-lite hash-lite mcp
  or: uvx --from git+https://github.com/tidybytetools/hash-lite hash-lite-mcp
"""
import os
from typing import Annotated, Literal
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
import hash_lite as lite

MAX_BYTES = 5_000_000  # 5 MB is plenty for local files

mcp = FastMCP("hash-lite")

READ_ONLY = dict(
    readOnlyHint=True,       # only reads; never writes or changes anything
    destructiveHint=False,
    idempotentHint=True,     # same input always gives the same hashes
    openWorldHint=False,     # no network; works on the text or local file you give it
)

Algo = Literal["sha256", "sha1", "md5", "sha512"]
Algorithms = Annotated[
    list[Algo] | None,
    Field(description="Hash algorithms to compute. Default: sha256, sha1, md5. SHA-512 is optional. MD5 and SHA-1 are provided because people still need them for checks; they are not safe for new security work."),
]


def _check_file(path: str) -> bytes:
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"file not found: {path}")
    if os.path.getsize(path) > MAX_BYTES:
        raise ValueError("file is bigger than 5 MB")
    with open(path, "rb") as f:
        return f.read()


@mcp.tool(
    title="Hash a text string",
    annotations=ToolAnnotations(title="Hash a text string", **READ_ONLY),
)
def hash_text(
    text: Annotated[str, Field(description="The text to hash. It is hashed as UTF-8 bytes.")],
    algorithms: Algorithms = None,
    include_base64: Annotated[bool, Field(description="If true (default), each hash is returned as hex and as Base64. Hex is always included.")] = True,
) -> dict:
    """Hash pasted text with SHA-256, SHA-1, MD5, and optional SHA-512.

    Use this when you have text in the conversation and need its checksum. The
    text is hashed as UTF-8 bytes. It is plain code, not an AI model, so the same
    text always gives the same hashes. This tool does not look the hash up in a
    malware list or a password list. Do not use it for a file on disk (use
    hash_file for files).

    algorithms: a list from sha256, sha1, md5, sha512. Default is sha256, sha1
    and md5. MD5 and SHA-1 are not safe for new security work; prefer SHA-256
    or SHA-512 when you can.

    Returns {"ok", "bytes", "encoding": "utf-8", "hashes", and a hex field for
    each algorithm, plus a Base64 field when include_base64 is true}.
    """
    return lite.hash_text(text, algorithms=algorithms, include_base64=include_base64)


@mcp.tool(
    title="Hash a local file",
    annotations=ToolAnnotations(title="Hash a local file", **READ_ONLY),
)
def hash_file(
    path: Annotated[str, Field(description="Full path to a local file, up to 5 MB. The raw file bytes are hashed, not a decoded string.")],
    algorithms: Algorithms = None,
    include_base64: Annotated[bool, Field(description="If true (default), each hash is returned as hex and as Base64. Hex is always included.")] = True,
) -> dict:
    """Hash a local file's raw bytes with SHA-256, SHA-1, MD5, and optional SHA-512.

    Use this when the data is in a file on this computer, so you don't have to
    paste it. The file is only read, never changed. Files larger than 5 MB are
    rejected; use the Apify version for bigger jobs. This tool does not look the
    hash up in a malware list or a password list.

    path: full path to a file, up to 5 MB.
    algorithms: a list from sha256, sha1, md5, sha512. Default is sha256, sha1
    and md5. MD5 and SHA-1 are not safe for new security work; prefer SHA-256
    or SHA-512 when you can.

    Returns {"ok", "bytes", "hashes", and a hex field for each algorithm, plus a
    Base64 field when include_base64 is true}.
    """
    data = _check_file(path)
    return lite.hash_file_bytes(data, algorithms=algorithms, include_base64=include_base64)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
