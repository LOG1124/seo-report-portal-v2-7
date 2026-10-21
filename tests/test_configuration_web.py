"""The setup UI must save only the intended local files and never disclose secrets."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from configuration_store import ConfigurationStore, ConfigurationError


class ConfigurationStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.workspace = self.root / 'workspace'
        self.home = self.root / 'codex'
        self.store = ConfigurationStore(self.workspace, self.home)

    def test_secret_saved_to_exact_file_and_absent_from_result_and_status(self):
        result = self.store.save('dataforseo', {'login': 'test-login', 'password': 'test-secret'})
        path = self.workspace / 'private/dataforseo.env'
        self.assertIn('DATAFORSEO_PASSWORD=test-secret', path.read_text())
        self.assertEqual(result['files'], [str(path)])
        self.assertNotIn('test-secret', json.dumps([result, self.store.status()]))
        self.assertIn('private/', (self.workspace / '.gitignore').read_text())

    def test_existing_credentials_require_explicit_replacement_and_backup(self):
        self.store.save('dataforseo', {'login': 'first', 'password': 'original'})
        path = self.workspace / 'private/dataforseo.env'
        original = path.read_bytes()
        with self.assertRaises(ConfigurationError):
            self.store.save('dataforseo', {'login': 'second', 'password': 'new'})
        self.assertEqual(path.read_bytes(), original)
        result = self.store.save('dataforseo', {'login': 'second', 'password': 'new', 'replace': True})
        self.assertEqual(Path(result['backups'][0]).read_bytes(), original)

    def test_invalid_input_and_symlink_do_not_write(self):
        for data in ({'login': 'x\nINJECT=1', 'password': 'a'}, {'login': 'x', 'password': ''}):
            with self.assertRaises(ConfigurationError):
                self.store.save('dataforseo', data)
        self.assertFalse(self.workspace.exists())
        self.workspace.mkdir()
        external = self.root / 'elsewhere'
        external.mkdir()
        try:
            (self.workspace / 'private').symlink_to(external, target_is_directory=True)
        except OSError:
            self.skipTest('symlinks unavailable')
        with self.assertRaises(ConfigurationError):
            self.store.save('dataforseo', {'login': 'x', 'password': 'a'})
        self.assertEqual(list(external.iterdir()), [])

    def test_mcp_merge_preserves_other_settings_and_backs_up(self):
        try:
            import tomllib
        except ImportError:
            self.skipTest('automatic MCP merge needs Python 3.11+')
        self.home.mkdir()
        config = self.home / 'config.toml'
        original = '# keep comment\nmodel = "keep-model"\n[mcp_servers.other]\nurl = "https://other.invalid"\n'
        config.write_text(original)
        result = self.store.save('seoagent', {'token': 'test-token', 'integrate': True})
        content = config.read_text()
        self.assertTrue(content.startswith(original))
        parsed = tomllib.loads(content)
        self.assertEqual(parsed['model'], 'keep-model')
        self.assertEqual(parsed['mcp_servers']['seoagent']['http_headers']['Authorization'], 'Bearer test-token')
        self.assertNotIn('test-token', json.dumps(result))
        self.assertTrue(any(Path(p).read_text() == original for p in result['backups']))

    def test_customer_configuration_is_not_a_web_operation(self):
        with self.assertRaises(ConfigurationError):
            self.store.save('google', {'domain': '../escape'})
        self.assertFalse(self.workspace.exists())

class ConfigurationBehaviorTests(unittest.TestCase):
    setUp = ConfigurationStoreTests.setUp
    def test_google_upload_places_shared_json_without_creating_customers(self):
        credential = {'type': 'service_account', 'client_email': 'reader@test.invalid',
                      'project_id': 'test-only', 'token_uri': 'https://oauth2.googleapis.com/token',
                      'private_key': '-----BEGIN PRIVATE KEY-----\nSYNTHETIC-NOT-A-KEY\n-----END PRIVATE KEY-----\n'}
        data = {'google_json': json.dumps(credential)}
        result = self.store.save('google_credentials', data)
        target = self.workspace / 'private/google-service-account.json'
        self.assertEqual(json.loads(target.read_text()), credential)
        self.assertEqual(result['files'], [str(target)])
        self.assertFalse((self.workspace / 'private/customers').exists())
        self.assertNotIn('SYNTHETIC', json.dumps(result))
        self.assertNotIn('reader@test.invalid', json.dumps(result))
        original = target.read_bytes()
        with self.assertRaises(ConfigurationError):
            self.store.save('google_credentials', data)
        data.update(replace=True, google_json='{"type":"service_account"}')
        with self.assertRaises(ConfigurationError):
            self.store.save('google_credentials', data)
        self.assertEqual(target.read_bytes(), original)

    def test_oss_configs_round_trip_and_keep_blank_secrets(self):
        from publish_oss_report import load_env_file
        data = {'access_key_id': 'test-id', 'access_key_secret': 'test-secret', 'region': 'oss-cn-test',
                'archive_root': 'Z:\\reports', 'source_root': 'Z:\\sources', 'ossutil_bin': 'ossutil'}
        self.store.save('oss', data)
        self.store.save('oss', {'replace': True, 'archive_root': 'Z:\\new-reports'})
        settings = load_env_file(self.workspace / 'private/oss.env')
        self.assertEqual(settings['OSS_ARCHIVE_ROOT'], 'Z:\\new-reports')
        self.assertEqual(settings['GOOGLE_SOURCE_ARCHIVE_ROOT'], 'Z:\\sources')
        self.assertIn('test-secret', (self.workspace / 'private/ossutilconfig').read_text())

    def test_source_paths_can_be_saved_without_publish_credentials(self):
        result = self.store.save('oss', {'source_root': 'Z:\\sources'})
        env = self.workspace / 'private/oss.env'
        self.assertEqual(result['files'], [str(env)])
        self.assertIn('GOOGLE_SOURCE_ARCHIVE_ROOT=Z:\\sources', env.read_text())
        self.assertFalse((self.workspace / 'private/ossutilconfig').exists())

    def test_group_failure_rolls_back_already_written_files(self):
        from unittest.mock import patch
        import configuration_store
        self.store.save('oss', {'access_key_id': 'id', 'access_key_secret': 'secret', 'region': 'region',
                                'archive_root': 'reports', 'source_root': 'sources'})
        env = self.workspace / 'private/oss.env'
        ini = self.workspace / 'private/ossutilconfig'
        old = (env.read_bytes(), ini.read_bytes())
        real = configuration_store.os.replace
        counter = 0
        def fail_second(source, target):
            nonlocal counter
            counter += 1
            if counter == 2:
                raise OSError('simulated disk failure')
            return real(source, target)
        with patch.object(configuration_store.os, 'replace', side_effect=fail_second):
            with self.assertRaises(ConfigurationError):
                self.store.save('oss', {'replace': True, 'region': 'updated'})
        self.assertEqual((env.read_bytes(), ini.read_bytes()), old)
        self.assertEqual(list(self.workspace.rglob('.seo-config-*')), [])

    def test_rollback_failure_is_reported_without_claiming_full_recovery(self):
        from unittest.mock import patch
        import configuration_store
        self.store.save('oss', {'access_key_id': 'id', 'access_key_secret': 'secret', 'region': 'region',
                                'archive_root': 'reports', 'source_root': 'sources'})
        real = configuration_store.os.replace
        count = 0
        def fail_after_first(source, target):
            nonlocal count
            count += 1
            if count >= 2:
                raise OSError('synthetic failure')
            return real(source, target)
        with patch.object(configuration_store.os, 'replace', side_effect=fail_after_first):
            with self.assertRaisesRegex(ConfigurationError, '自动恢复未全部完成'):
                self.store.save('oss', {'replace': True, 'region': 'updated', 'archive_root': 'new-reports'})
        self.assertTrue(list((self.workspace / 'private/config-backups').rglob('oss.env')))
        self.assertEqual(list(self.workspace.rglob('.seo-restore-*')), [])

    def test_shared_status_never_reads_or_lists_customer_configs(self):
        folder = self.workspace / 'private/customers/example.com'
        folder.mkdir(parents=True)
        customer = folder / 'google-api.json'
        customer.write_text('customer-specific-content')
        status = self.store.status()
        self.assertNotIn('customers/', json.dumps(status))
        self.assertNotIn('customer-specific-content', json.dumps(status))
        self.assertEqual(customer.read_text(), 'customer-specific-content')

    def test_mcp_existing_target_preserves_extra_headers_and_comments(self):
        try:
            import tomllib
        except ImportError:
            self.skipTest('automatic MCP merge needs Python 3.11+')
        from configuration_store import merge_mcp
        original = '# keep\nmodel="stable"\n[mcp_servers.seoagent]\nenabled=false\nurl="https://old.invalid"\nstartup_timeout_sec=30\n[mcp_servers.seoagent.http_headers]\nAuthorization="Bearer old"\nX-Team="keep"\n[mcp_servers.other]\nurl="https://other.invalid"\n'
        value = merge_mcp(original, 'replacement')
        parsed = tomllib.loads(value)
        self.assertEqual(parsed['mcp_servers']['seoagent']['http_headers']['X-Team'], 'keep')
        self.assertIn('# keep\nmodel="stable"', value)
        self.assertEqual(parsed['mcp_servers']['seoagent']['startup_timeout_sec'], 30)
        with self.assertRaises(ConfigurationError):
            merge_mcp('broken = [', 'replacement')
        with self.assertRaisesRegex(ConfigurationError, '本地命令传输'):
            merge_mcp('[mcp_servers.seoagent]\ncommand="legacy"\nargs=[]\n', 'replacement')


class ConfigurationHTTPTests(unittest.TestCase):
    def setUp(self):
        import threading
        from configure_web import ConfigurationServer
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name).resolve()
        self.server = ConfigurationServer(ConfigurationStore(root / 'workspace', root / 'codex'))
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={'poll_interval': .01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.thread.join(2)
        self.server.server_close()

    def request(self, path, data=None, **headers):
        from http.client import HTTPConnection
        connection = HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        if data is not None:
            headers.setdefault('Content-Type', 'application/json')
        connection.request('POST' if data is not None else 'GET', path,
                           json.dumps(data) if data is not None else None, headers)
        response = connection.getresponse()
        body = response.read().decode()
        status, response_headers = response.status, dict(response.getheaders())
        connection.close()
        return status, body, response_headers

    def test_token_origin_and_host_are_required_for_saving(self):
        path = '/api/save/dataforseo'
        data = {'login': 'user', 'password': 'test-secret'}
        self.assertEqual(self.request(path, data)[0], 403)
        self.assertEqual(self.request(path, data, Origin='https://evil.invalid', **{'X-Setup-Token': self.server.token})[0], 403)
        self.assertEqual(self.request('/api/status', Host='evil.invalid', **{'X-Setup-Token': self.server.token})[0], 403)
        self.assertFalse(self.server.store.workspace.exists())
        status, body, headers = self.request(path, data, Origin=self.server.origin, **{'X-Setup-Token': self.server.token})
        self.assertEqual(status, 200)
        self.assertNotIn('test-secret', body)
        self.assertEqual(headers['Cache-Control'], 'no-store')
        status, body, _ = self.request('/api/status', **{'X-Setup-Token': self.server.token})
        self.assertEqual(status, 200)
        self.assertNotIn('test-secret', body)
        self.assertEqual(self.request('/private/dataforseo.env')[0], 404)

    def test_html_is_static_and_has_no_external_assets(self):
        status, html, headers = self.request('/')
        self.assertEqual(status, 200)
        self.assertNotIn(self.server.token, html)
        self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
        self.assertNotIn('src="http', html)
        self.assertNotIn('href="http', html)
        for name in ('domain', 'property_id', 'gsc_site_url', 'report_start', 'report_end'):
            self.assertNotIn(f'name="{name}"', html)
        self.assertIn('data-group="google_credentials"', html)

    def test_expired_session_cannot_write(self):
        self.server.expires = 0
        status, _, _ = self.request('/api/save/dataforseo', {'login': 'x', 'password': 'y'},
                                    Origin=self.server.origin, **{'X-Setup-Token': self.server.token})
        self.assertEqual(status, 403)
        self.assertFalse(self.server.store.workspace.exists())


if __name__ == '__main__':
    unittest.main()
