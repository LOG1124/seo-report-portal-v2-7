"""Offline setup must preserve configured secrets and customer isolation."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from setup_workspace import setup_workspace


class SetupWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.output = contextlib.redirect_stdout(io.StringIO())
        self.output.__enter__()
        self.addCleanup(self.output.__exit__, None, None, None)

    def test_creates_ready_named_templates_and_customer_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_workspace(root, 'example.com')
            for name in ('google-service-account.json', 'dataforseo.env', 'oss.env',
                         'ossutilconfig', 'seoagent-mcp.toml'):
                self.assertTrue((root / 'private' / name).is_file(), name)
            customer = root / 'private/customers/example.com'
            self.assertEqual(json.loads((customer / 'project-input.json').read_text())['website_url'], '')
            self.assertTrue((customer / 'google-api.json').is_file())
            self.assertIn('private/', (root / '.gitignore').read_text())
            self.assertFalse((root / 'customer-registry.json').exists())

    def test_repeat_keeps_existing_bytes_and_never_prints_secrets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            setup_workspace(root, 'example.com')
            secret = root / 'private/dataforseo.env'
            secret.write_bytes(b'DATAFORSEO_PASSWORD=local-secret-sentinel\r\n')
            ignore = root / '.gitignore'
            ignore.write_text('custom-rule\n')
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                setup_workspace(root, 'another.com')
            self.assertEqual(secret.read_bytes(), b'DATAFORSEO_PASSWORD=local-secret-sentinel\r\n')
            self.assertNotIn('local-secret-sentinel', output.getvalue())
            self.assertTrue(ignore.read_text().startswith('custom-rule\n'))
            setup_workspace(root, 'another.com')
            self.assertEqual(ignore.read_text().count('private/'), 1)

    def test_invalid_domain_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with self.assertRaises(ValueError):
                setup_workspace(root, '../outside')
            self.assertEqual(list(root.iterdir()), [])

    def test_symlinked_private_is_rejected_without_external_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'workspace'
            external = Path(tmp) / 'external'
            root.mkdir()
            external.mkdir()
            try:
                (root / 'private').symlink_to(external, target_is_directory=True)
            except OSError:
                self.skipTest('本机未授予创建符号链接权限')
            with self.assertRaises(ValueError):
                setup_workspace(root, 'example.com')
            self.assertEqual(list(external.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
