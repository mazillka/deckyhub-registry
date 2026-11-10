import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import audit_deps


class DependencyAuditTests(unittest.TestCase):
    def archive(self, files):
        tmp = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
        tmp.close()
        self.addCleanup(Path(tmp.name).unlink, missing_ok=True)
        with zipfile.ZipFile(tmp.name, "w") as z:
            for path, content in files.items():
                z.writestr(path, content)
        return tmp.name

    def test_installed_metadata_and_vulnerabilities(self):
        path = self.archive({"plugin/node_modules/@scope/foo/package.json": json.dumps({"name": "@scope/foo", "version": "1.2.3"}),
                             "plugin/lib/requests-2.0.dist-info/METADATA": "Name: requests\nVersion: 2.0\n"})
        calls = []
        def query(items):
            calls.extend(items)
            return {"results": [{"vulns": [{"id": "GHSA-test"}]}, {}]}
        result = audit_deps.audit_dependencies(path, query)
        self.assertEqual(result["result"], "incomplete")
        self.assertEqual([p["name"] for p in result["packages"]], ["@scope/foo", "requests"])
        self.assertEqual(result["findings"][0]["id"], "GHSA-test")
        self.assertEqual(calls[0], {"package": {"ecosystem": "npm", "name": "@scope/foo"}, "version": "1.2.3"})

    def test_lockfiles_and_project_manifests_are_not_inventory(self):
        path = self.archive({"package-lock.json": '{"packages":{"node_modules/a":{"version":"1.0.0"}}}',
                             "package.json": '{"name":"app","version":"1.0.0"}', "lib/native.so": b"binary"})
        result = audit_deps.audit_dependencies(path, lambda _: self.fail("unexpected query"))
        self.assertEqual(result["packages"], [])
        self.assertEqual(result["result"], "incomplete")
        self.assertTrue(any("binary" in i for i in result["issues"]))

    def test_invalid_and_unreadable_metadata(self):
        path = self.archive({"node_modules/foo/package.json": '{"name":"foo","version":"^1.2.3"}',
                             "x.dist-info/METADATA": "Name: a\nName: b\nVersion: 1.0\n"})
        result = audit_deps.audit_dependencies(path, lambda _: self.fail("unexpected query"))
        self.assertEqual(result["packages"], [])
        self.assertTrue(any("metadata" in i for i in result["issues"]))

    def test_query_failure_and_pagination_are_incomplete(self):
        path = self.archive({"node_modules/foo/package.json": '{"name":"foo","version":"1.2.3"}'})
        def failure(_):
            raise OSError("offline")
        for response in (failure, lambda _: {"results": [{"next_page_token": "next"}]},
                         lambda _: {"results": []}):
            result = audit_deps.audit_dependencies(path, response)
            self.assertEqual(result["result"], "incomplete")
            self.assertGreaterEqual(len(result["issues"]), 2)

    def test_binary_headers_include_extensionless_files(self):
        pe = bytearray(132)
        pe[:2] = b"MZ"
        pe[60:64] = (128).to_bytes(4, "little")
        pe[128:132] = b"PE\0\0"
        path = self.archive({"bin/tool": b"\x7fELF" + bytes(20),
                             "bin/windows": pe,
                             "lib/darwin": b"\xcf\xfa\xed\xfe" + bytes(12),
                             "fake.exe": b"not executable"})
        result = audit_deps.audit_dependencies(path)
        self.assertEqual(result["binaries"], [
            {"path": "bin/tool", "size": 24, "format": "ELF"},
            {"path": "bin/windows", "size": 132, "format": "PE"},
            {"path": "lib/darwin", "size": 16, "format": "Mach-O"}])
        self.assertEqual(result["result"], "incomplete")

    def test_binary_limit_and_truncated_header(self):
        path = self.archive({"a": b"\x7fELF" + bytes(20),
                             "b": b"\x7fELF" + bytes(20),
                             "truncated": b"\x7fELF"})
        with patch.object(audit_deps, "MAX_BINARIES", 1):
            result = audit_deps.audit_dependencies(path)
        self.assertEqual(len(result["binaries"]), 1)
        self.assertTrue(any("inventory limit" in i for i in result["issues"]))
        self.assertTrue(any("truncated" in i for i in result["issues"]))
        self.assertEqual(result["result"], "incomplete")

    def test_corrupt_archive_is_error(self):
        with tempfile.NamedTemporaryFile() as f:
            self.assertEqual(audit_deps.audit_dependencies(f.name)["result"], "error")


if __name__ == "__main__":
    unittest.main()
