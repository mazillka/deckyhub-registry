import unittest

from scripts.audit_rules import scan_text


class AuditRulesTests(unittest.TestCase):
    def test_python_direct_sensitive_reads_and_line(self):
        text = '# open("/etc/shadow")\nopen("/etc/shadow")\nPath("~/.ssh/id_ed25519")\n'
        self.assertEqual(scan_text('main.py', text), [
            {'rule': 'sensitive_file_read', 'path': 'main.py', 'line': 2},
        ])

    def test_python_comments_strings_and_ordinary_files(self):
        text = '''"""open('/etc/shadow')"""\nexample = "open('/etc/shadow')"\n# open('/etc/shadow')\nopen('/etc/passwd')\nopen(variable)\n'''
        self.assertEqual(scan_text('main.py', text), [])

    def test_shell_rules(self):
        text = 'cat /etc/shadow\ncrontab -e\nsystemctl --user enable demo.service\nchmod u+s binary\ntee /etc/sudoers.d/demo\n'
        self.assertEqual([item['rule'] for item in scan_text('install.sh', text)], [
            'sensitive_file_read', 'persistence_crontab', 'persistence_systemd_enable',
            'privilege_setuid', 'privilege_sudoers'])

    def test_shell_comments_literals_and_routine_sudo(self):
        text = '# crontab -e\necho "systemctl enable demo"\nsudo systemctl restart demo\nsudo chmod 755 binary\ncat /etc/passwd # /etc/shadow\n'
        self.assertEqual(scan_text('install.sh', text), [])
        self.assertEqual(scan_text('README.md', 'open("/etc/shadow")\ncrontab -e'), [])

    def test_malformed_python_does_not_report_strings(self):
        self.assertEqual(scan_text('bad.py', '""" open("/etc/shadow")'), [])


if __name__ == '__main__':
    unittest.main()
