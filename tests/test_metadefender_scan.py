import hashlib
import io
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import metadefender_scan as md


class MetaDefenderTests(unittest.TestCase):
    digest = hashlib.sha256(b"archive").hexdigest()
    url = "https://github.com/a/b/releases/download/v1/plugin.zip"

    def test_existing_report_is_recorded_without_upload(self):
        class Client:
            def request(self, path):
                assert path == "/hash/" + MetaDefenderTests.digest
                return {"data_id": "abc", "scan_results": {"progress_percentage": 100, "total_detected_avs": 2, "total_avs": 20}}
        self.assertEqual(md.process(Client(), self.digest, self.url, {})["flagged"], 2)

    def test_unknown_hash_uploads_and_pending_is_polled(self):
        class Client:
            def request(self, path):
                if path.startswith("/hash/"):
                    raise urllib.error.HTTPError(path, 404, "missing", {}, None)
                return {"data_id": "abc", "scan_results": {"progress_percentage": 100, "total_detected_avs": 0, "total_avs": 20, "scan_all_result_i": 0}}
            def upload(self, url, digest):
                return {"state": "pending", "dataId": "abc"}
        pending = md.process(Client(), self.digest, self.url, {})
        self.assertEqual(pending["state"], "pending")
        self.assertEqual(md.process(Client(), self.digest, self.url, pending)["state"], "complete")

    def test_pending_uploads_are_polled_before_new_hashes(self):
        new, pending = "a" * 64, "b" * 64
        with tempfile.TemporaryDirectory() as folder:
            scans, reports = Path(folder) / "scans.json", Path(folder) / "reports.json"
            scans.write_text('{"files": {"https://github.com/a/b/releases/download/v1/new.zip": {"sha256": "%s"}, "https://github.com/a/b/releases/download/v1/old.zip": {"sha256": "%s"}}}' % (new, pending), encoding="utf-8")
            reports.write_text('{"reports": {"%s": {"state": "pending", "dataId": "abc", "checkedAt": 1793804000}}}' % pending, encoding="utf-8")
            seen = []
            def process(client, digest, url, previous):
                seen.append(digest)
                raise md.BudgetExhausted  # the budget runs out after the first one
            with patch.dict("os.environ", {"METADEFENDER_API_KEY": "key"}), patch.object(md, "process", process), patch("sys.stdout", io.StringIO()):
                md.main(scans, reports)
        self.assertEqual(seen, [pending])

    def test_partial_or_missing_results_are_not_clean(self):
        class Client:
            def request(self, path):
                return {"data_id": "abc", "scan_results": {"progress_percentage": 100, "total_detected_avs": 0, "total_avs": 0}}
        self.assertEqual(md.process(Client(), self.digest, self.url, {})["state"], "waiting")

    def test_incomplete_scan_with_zero_detections_is_not_clean(self):
        class Client:
            def request(self, path):
                return {"data_id": "abc", "scan_results": {"progress_percentage": 100, "total_detected_avs": 0, "total_avs": 20, "scan_all_result_i": 12}}
        self.assertEqual(md.process(Client(), self.digest, self.url, {})["state"], "waiting")

    def test_upload_checks_hash_before_submission(self):
        client = md.MetaDefender("secret")
        class Response(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *args): self.close()
        class Opener:
            def open(self, url, timeout): return Response(b"different")
        with patch.object(md.urllib.request, "build_opener", return_value=Opener()), patch.object(client, "request") as request:
            with self.assertRaises(ValueError): client.upload(self.url, self.digest)
            request.assert_not_called()

    def test_rejects_insecure_redirect_and_unknown_api(self):
        with self.assertRaises(ValueError):
            md.HttpsRedirect().redirect_request(None, None, 302, "", {}, "http://example.com/file")
        with self.assertRaises(ValueError):
            md.MetaDefender("secret").request("/file/../../other")


if __name__ == "__main__": unittest.main()
