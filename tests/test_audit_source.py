import io
import os
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
import audit_source


def archive(files):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)
    return buffer.getvalue()


class SourceComparisonTests(unittest.TestCase):
    def compare(self, plugin, source, repo='owner/repo', tag='v1.0'):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'plugin.zip')
            with open(path, 'wb') as f:
                f.write(archive(plugin))
            return audit_source.compare_source(path, repo, tag, lambda url: source)

    def test_exact_tag_and_matching_code(self):
        urls = []
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'plugin.zip')
            with open(path, 'wb') as f:
                f.write(archive({'main.py': 'print(1)'}))
            result = audit_source.compare_source(path, 'owner/repo', 'release/v1',
                lambda url: urls.append(url) or archive({'repo-release/main.py': 'print(1)'}))
        self.assertEqual(result, {'result': 'complete', 'findings': [], 'tag': 'release/v1'})
        self.assertEqual(urls, ['https://codeload.github.com/owner/repo/zip/refs/tags/release%2Fv1'])

    def test_missing_and_different(self):
        result = self.compare({'main.py': 'new', 'other.sh': 'x'}, archive({'r/main.py': 'old'}))
        self.assertEqual(result['result'], 'complete')
        self.assertEqual(result['findings'], [{'rule': 'source_file_differs', 'path': 'main.py'},
                                             {'rule': 'source_path_missing', 'path': 'other.sh'}])

    def test_excluded_content_marks_incomplete(self):
        result = self.compare({'main.py': 'x', 'dist/index.js': 'generated'}, archive({'r/main.py': 'x'}))
        self.assertEqual(result['result'], 'incomplete')
        self.assertEqual(result['findings'], [])

    def test_large_non_code_source_asset_does_not_block_code_comparison(self):
        from unittest.mock import patch
        with patch.object(audit_source, 'MAX_MEMBER', 10):
            result = self.compare({'main.py': 'x'}, archive({'r/main.py': 'x', 'r/image.png': 'x' * 100}))
        self.assertEqual(result['result'], 'complete')
        self.assertEqual(result['findings'], [])

    def test_bad_input_and_unavailable(self):
        for repo, tag in [('x/../y', 'v1'), ('owner/repo', '../main'), ('owner/repo', '')]:
            self.assertEqual(self.compare({'main.py': 'x'}, b'', repo, tag)['result'], 'error')
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, 'plugin.zip')
            with open(path, 'wb') as f:
                f.write(archive({'main.py': 'x'}))
            def fail(url):
                raise OSError('network unavailable')
            result = audit_source.compare_source(path, 'owner/repo', 'v1', fail)
            self.assertEqual(result['result'], 'error')
            self.assertIn('unavailable', result['reason'])

    def test_unsafe_archive_and_symlink_rejected(self):
        self.assertEqual(self.compare({'../main.py': 'x'}, archive({'r/main.py': 'x'}))['result'], 'error')
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as z:
            info = zipfile.ZipInfo('r/main.py'); info.create_system = 3
            info.external_attr = (0o120777 << 16)
            z.writestr(info, 'target')
        self.assertEqual(self.compare({'main.py': 'x'}, buffer.getvalue())['result'], 'error')

    def test_findings_are_bounded(self):
        plugin = {f'file{i}.py': 'x' for i in range(101)}
        result = self.compare(plugin, archive({'r/unrelated.py': 'x'}))
        self.assertEqual(result['result'], 'incomplete')
        self.assertEqual(len(result['findings']), 100)
        self.assertIn('truncated', result['reason'])
        self.assertEqual(result['tag'], 'v1.0')

    def test_single_source_directory_is_not_a_wrapper(self):
        result = self.compare({'src/main.py': 'x'}, archive({'r/src/main.py': 'x'}))
        self.assertEqual(result, {'result': 'complete', 'findings': [], 'tag': 'v1.0'})

    def test_wrapped_release(self):
        result = self.compare({'plugin/plugin.json': '{}', 'plugin/main.py': 'x'}, archive({'r/main.py': 'x'}))
        self.assertEqual(result['result'], 'incomplete')
        self.assertEqual(result['findings'], [])


if __name__ == '__main__':
    unittest.main()
