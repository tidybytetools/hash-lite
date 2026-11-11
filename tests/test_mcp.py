"""Starts the MCP server over stdio (both ways it can start), lists tools, and calls them."""
import asyncio, json, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    ClientSession = None

READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


def _data(res):
    """The tool result as Python data (structured content if present, else the JSON text)."""
    if res.structuredContent is not None:
        sc = res.structuredContent
        return sc.get("result", sc) if set(sc) == {"result"} else sc
    return json.loads(res.content[0].text)


async def _session(args, fn):
    params = StdioServerParameters(command=sys.executable, args=args, cwd=ROOT)
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            return await fn(s)


@unittest.skipIf(ClientSession is None, "mcp not installed")
class MCP(unittest.TestCase):
    def test_tools_and_annotations(self):
        async def go(s):
            return (await s.list_tools()).tools
        tools = asyncio.run(_session([os.path.join(ROOT, "hash_lite_mcp.py")], go))
        self.assertEqual(sorted(t.name for t in tools), ["hash_file", "hash_text"])
        for t in tools:
            self.assertTrue(t.title)
            self.assertIn("Use this when", t.description)
            for k, v in READ_ONLY.items():
                self.assertIs(getattr(t.annotations, k), v, f"{t.name} {k}")

    def test_calls(self):
        async def go(s):
            hello = await s.call_tool("hash_text", {"text": "hello world"})
            sha_only = await s.call_tool("hash_text", {"text": "hello world", "algorithms": ["sha256"], "include_base64": False})
            f = await s.call_tool("hash_file", {"path": os.path.join(HERE, "fixtures", "abc.bin"), "algorithms": ["sha256"], "include_base64": False})
            missing = await s.call_tool("hash_file", {"path": "/nope/missing.bin"})
            empty = await s.call_tool("hash_text", {"text": ""})
            bad = await s.call_tool("hash_text", {"text": "x", "algorithms": ["blake3"]})
            return hello, sha_only, f, missing, empty, bad
        hello, sha_only, f, missing, empty, bad = asyncio.run(_session([os.path.join(ROOT, "hash_lite_mcp.py")], go))
        self.assertEqual(_data(hello)["sha256"], "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9")
        self.assertIn("sha256Base64", _data(hello))
        self.assertEqual(_data(sha_only)["sha256"], "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9")
        self.assertNotIn("sha256Base64", _data(sha_only))
        self.assertEqual(_data(f)["sha256"], "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
        self.assertTrue(missing.isError)
        self.assertTrue(empty.isError)
        self.assertTrue(bad.isError)

    def test_cli_mcp_subcommand_starts_server(self):
        async def go(s):
            return [t.name for t in (await s.list_tools()).tools]
        names = asyncio.run(_session([os.path.join(ROOT, "hash_lite.py"), "mcp"], go))
        self.assertIn("hash_text", names)


if __name__ == "__main__":
    unittest.main()
