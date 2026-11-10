"""Bounded, static release ZIP comparison with the exact GitHub tag archive.

Matching files do not establish that a release was built from this source.
"""
import io
import re
import stat
import urllib.parse
import urllib.request
import zipfile

MAX_ARCHIVE = 40 * 1024 * 1024
MAX_TOTAL = 120 * 1024 * 1024
MAX_MEMBER = 4 * 1024 * 1024
MAX_FILES = 5000
MAX_FINDINGS = 100
_CODE = {'.py', '.sh', '.bash', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.lua', '.rb', '.pl', '.php'}
_EXCLUDED_DIRS = {'node_modules', 'vendor', 'dist', 'build', '.git', '__pycache__', '.venv', 'venv'}
_REPO = re.compile(r'^[A-Za-z0-9](?:[A-Za-z0-9_.-]{0,98})/[A-Za-z0-9_][A-Za-z0-9_.-]{0,99}$')
_TAG = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_.+/-]{0,199}$')
_SAFE_REASONS = {'unsafe archive path', 'archive has too many members', 'archive contains a non-regular file',
                 'archive contains an encrypted file', 'archive exceeds uncompressed size limit',
                 'archive has duplicate paths', 'source archive has ambiguous root',
                 'source archive exceeds size limit', 'source archive exceeds size limit or is invalid'}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'DeckyHub-source-audit'})
    with urllib.request.build_opener(_NoRedirect()).open(request, timeout=20) as response:
        data = response.read(MAX_ARCHIVE + 1)
    if len(data) > MAX_ARCHIVE:
        raise ValueError('source archive exceeds size limit')
    return data


def _safe_parts(name):
    if '\\' in name or name.startswith('/') or any(ord(c) < 32 or ord(c) == 127 for c in name):
        raise ValueError('unsafe archive path')
    parts = name.rstrip('/').split('/')
    if any(part in ('', '.', '..') for part in parts) or ':' in parts[0]:
        raise ValueError('unsafe archive path')
    return parts


def _index(archive, source=False):
    entries = archive.infolist()
    if len(entries) > MAX_FILES:
        raise ValueError('archive has too many members')
    result = {}
    total = 0
    roots = set()
    for entry in entries:
        parts = _safe_parts(entry.filename)
        if source:
            roots.add(parts[0])
            if len(parts) == 1:
                continue
            parts = parts[1:]
        if entry.is_dir():
            continue
        mode = entry.external_attr >> 16
        if stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFREG)):
            raise ValueError('archive contains a non-regular file')
        if entry.flag_bits & 1:
            raise ValueError('archive contains an encrypted file')
        path = '/'.join(parts)
        # Source assets we never read need not consume the code-comparison budget.
        if source and (_excluded(path) or not any(path.lower().endswith(ext) for ext in _CODE)):
            continue
        total += entry.file_size
        if entry.file_size > MAX_MEMBER or total > MAX_TOTAL:
            raise ValueError('archive exceeds uncompressed size limit')
        if path in result:
            raise ValueError('archive has duplicate paths')
        result[path] = entry
    if source and len(roots) != 1:
        raise ValueError('source archive has ambiguous root')
    return result


def _excluded(path):
    parts = path.lower().split('/')
    return (bool(set(parts[:-1]) & _EXCLUDED_DIRS) or
            parts[-1].endswith(('.min.js', '.bundle.js', '.map')))


def compare_source(plugin_zip_path, repo, tag, fetch=None):
    """Compare code files at matching paths; fetch, when supplied, takes a URL.

    Findings mean only that an eligible file differs or was absent at its path.
    Skipped files and ambiguous layouts yield incomplete, never source equivalence.
    """
    if (not isinstance(repo, str) or not _REPO.fullmatch(repo) or
            any(part in ('.', '..') or part.endswith('.') for part in repo.split('/')) or
            not isinstance(tag, str) or not _TAG.fullmatch(tag) or
            '..' in tag or '//' in tag or tag.endswith(('/', '.', '.lock'))):
        return {'result': 'error', 'findings': [], 'reason': 'invalid repository or release tag'}
    url = 'https://codeload.github.com/{}/zip/refs/tags/{}'.format(
        repo, urllib.parse.quote(tag, safe=''))
    try:
        data = (fetch or _fetch)(url)
        if not isinstance(data, bytes) or len(data) > MAX_ARCHIVE:
            raise ValueError('source archive exceeds size limit or is invalid')
        with zipfile.ZipFile(io.BytesIO(data)) as source_zip, zipfile.ZipFile(plugin_zip_path) as plugin_zip:
            source = _index(source_zip, source=True)
            plugin = _index(plugin_zip)
            # Decky release ZIPs commonly wrap the plugin in one directory.
            paths = list(plugin)
            if paths and all('/' in path for path in paths):
                roots = {path.split('/', 1)[0] for path in paths}
                if len(roots) == 1 and any(path.split('/', 1)[1] == 'plugin.json' for path in paths):
                    plugin = {path.split('/', 1)[1]: entry for path, entry in plugin.items()}
            findings = []
            skipped = False
            checked = 0
            truncated = False
            for path, entry in sorted(plugin.items()):
                if _excluded(path):
                    skipped = True
                    continue
                if not any(path.lower().endswith(ext) for ext in _CODE):
                    skipped = True
                    continue
                checked += 1
                other = source.get(path)
                if other is None:
                    if len(findings) < MAX_FINDINGS:
                        findings.append({'rule': 'source_path_missing', 'path': path})
                    else:
                        truncated = True
                elif plugin_zip.read(entry) != source_zip.read(other):
                    if len(findings) < MAX_FINDINGS:
                        findings.append({'rule': 'source_file_differs', 'path': path})
                    else:
                        truncated = True
            if skipped or not checked or truncated:
                reason = 'generated, dependency, non-code, or no comparable files; source equivalence is not established'
                if truncated:
                    reason += '; findings truncated'
                return {'result': 'incomplete', 'findings': findings, 'tag': tag, 'reason': reason}
            return {'result': 'complete', 'findings': findings, 'tag': tag}
    except (OSError, ValueError, zipfile.BadZipFile, RuntimeError, EOFError, NotImplementedError, OverflowError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) and str(exc) in _SAFE_REASONS else type(exc).__name__
        return {'result': 'error', 'findings': [], 'reason': 'source comparison unavailable: ' + detail}
