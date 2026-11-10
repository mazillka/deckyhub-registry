"""Narrow heuristic checks; findings are leads, not proof of malicious behavior.

Rule IDs: sensitive_file_read (direct reads of selected credential files),
persistence_crontab (crontab replacement/edit), persistence_systemd_enable
(systemd unit enablement), privilege_setuid (setuid permission changes), and
privilege_sudoers (direct writes to sudoers). Coverage is deliberately limited.
"""

import io
import re
import tokenize

_SENSITIVE = r'(?:/etc/(?:shadow|gshadow)|(?:~|\$HOME|/home/[^/\s"\']+)/\.ssh/(?:id_(?:rsa|ed25519|ecdsa|dsa)|authorized_keys)|(?:~|\$HOME|/home/[^/\s"\']+)/\.aws/credentials)'
_SHELL = re.compile(r'^\s*(?:sudo\s+)?(?P<command>crontab\s+(?:-e\b|-r\b|[^-\s#][^#]*)|systemctl\s+(?:--user\s+)?enable\b|chmod\s+(?:[ugoa]*\+s\b|[0-7]*[46][0-7]{3}\b))')
_READ = re.compile(r'\b(?:open|io\.open)\s*\(')
_PATH = re.compile(_SENSITIVE)
_WRITE_SUDOERS = re.compile(r'(?<![\w/])(?:/etc/sudoers(?:\.d/[^\s"\']+)?)')


def _python_mask(text):
    """Mask strings and comments, preserving positions and newlines."""
    lines = text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    masked = list(text)
    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in tokens:
            if token.type not in (tokenize.STRING, tokenize.COMMENT):
                continue
            start = offsets[token.start[0] - 1] + token.start[1]
            end = offsets[token.end[0] - 1] + token.end[1]
            for i in range(start, min(end, len(masked))):
                if masked[i] not in '\r\n':
                    masked[i] = ' '
    except (tokenize.TokenError, IndentationError, SyntaxError):
        # A malformed file cannot be reliably distinguished from literal text.
        return None
    return ''.join(masked)


def scan_text(path: str, text: str) -> list[dict]:
    """Return rule, archive path and one-based line for actionable heuristics."""
    findings = []
    suffix = path.lower().rsplit('.', 1)[-1] if '.' in path else ''
    if suffix == 'py':
        mask = _python_mask(text)
        if mask is None:
            return findings
        for match in _READ.finditer(mask):
            # Only direct literal arguments; do not speculate about variables.
            rest = text[match.end():].split('\n', 1)[0]
            literal = re.match(r'''\s*[rubfRUBF]*(["'])(.*?)\1''', rest)
            if literal and _PATH.search(literal.group(2)):
                findings.append({'rule': 'sensitive_file_read', 'path': path,
                                 'line': text.count('\n', 0, match.start()) + 1})
    elif suffix in ('sh', 'bash') or path.rsplit('/', 1)[-1] in ('install', 'uninstall'):
        for line_number, line in enumerate(text.splitlines(), 1):
            # Only commands starting a line are recognized; documentation and echo
            # strings do not become executable commands through this heuristic.
            command = _SHELL.match(line)
            rule = None
            if command:
                token = command.group('command')
                if token.startswith('crontab'):
                    rule = 'persistence_crontab'
                elif token.startswith('systemctl'):
                    rule = 'persistence_systemd_enable'
                else:
                    rule = 'privilege_setuid'
            elif re.match(r'^\s*(?:sudo\s+)?(?:cat|head|tail)\s+', line) and _PATH.search(line.split('#', 1)[0]):
                rule = 'sensitive_file_read'
            elif re.match(r'^\s*(?:sudo\s+)?(?:tee|install|cp)\s+', line) and _WRITE_SUDOERS.search(line.split('#', 1)[0]):
                rule = 'privilege_sudoers'
            if rule:
                findings.append({'rule': rule, 'path': path, 'line': line_number})
    return findings
