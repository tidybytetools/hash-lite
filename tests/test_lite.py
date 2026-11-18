import io, os, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import hash_lite as hl

class T(unittest.TestCase):
    def test_hello_sha256(self):
        r = hl.hash_text("hello world")
        self.assertEqual(r["bytes"], 11)
        self.assertEqual(r["sha256"], "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9")
        self.assertEqual(r["sha1"], "2aae6c35c94fcfb415dbe95f408b9ce91ee846ed")
        self.assertEqual(r["md5"], "5eb63bbbe01eeed093cb22bb8f5acdc3")
        self.assertTrue(r["sha256Base64"])
        self.assertEqual(r["encoding"], "utf-8")
        self.assertTrue(r["ok"])

    def test_empty_text(self):
        with self.assertRaises(ValueError):
            hl.hash_text("")

    def test_file_bytes_and_sha512(self):
        r = hl.hash_bytes(b"abc", algorithms=["sha256", "sha512"], include_base64=False)
        self.assertIn("sha512", r["hashes"])
        self.assertNotIn("sha512Base64", r)
        self.assertEqual(r["sha256"], "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_bad_algo(self):
        with self.assertRaises(ValueError):
            hl.hash_bytes(b"x", algorithms=["blake3"])

    def test_parse_algorithms_default_and_dedupe(self):
        self.assertEqual(hl.parse_algorithms(None), ["sha256", "sha1", "md5"])
        self.assertEqual(hl.parse_algorithms("SHA256, sha256, md5"), ["sha256", "md5"])

    def test_parse_algorithms_empty(self):
        with self.assertRaises(ValueError):
            hl.parse_algorithms("")

    def run_main(self, argv, stdin_text=""):
        out, err = io.StringIO(), io.StringIO()
        old = sys.stdin
        raw = stdin_text.encode("utf-8")
        sys.stdin = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8")
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = hl.main(argv)
        finally:
            sys.stdin = old
        return code, out.getvalue(), err.getvalue()

    def test_cli_json_text(self):
        code, out, err = self.run_main(["--json"], "hello world")
        self.assertEqual(code, 0)
        self.assertIn('"ok": true', out)
        self.assertIn("b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9", out)
        self.assertNotIn("apify.com", out)

    def test_cli_file_bytes(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "abc.bin")
            with open(path, "wb") as f:
                f.write(b"abc")
            code, out, err = self.run_main(["--json", "--algorithms", "sha256", "--no-base64", path])
            self.assertEqual(code, 0)
            self.assertIn("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", out)
            self.assertNotIn("Base64", out)

    def test_cli_help_has_apify_link(self):
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit):
            hl.main(["--help"])
        self.assertIn("https://apify.com/tidybytetools/hash-checksum", out.getvalue())

    def test_bad_file(self):
        code, out, err = self.run_main(["--json", "/nope/missing.bin"])
        self.assertEqual(code, 1)
        self.assertIn('"ok": false', out)

    def test_empty_stdin_json(self):
        code, out, err = self.run_main(["--json"], "")
        self.assertEqual(code, 1)
        self.assertIn('"ok": false', out)

    def test_version(self):
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
            hl.main(["--version"])
        self.assertIn(ctx.exception.code, (0, None))
        self.assertIn("1.0.1", out.getvalue())


if __name__ == "__main__":
    unittest.main()
