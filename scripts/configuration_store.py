"""Fixed-target local configuration storage for the first-run web form."""
from __future__ import annotations

import configparser
from copy import deepcopy
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import re
import tempfile
import uuid

from publish_oss_report import load_env_file

PACKAGE = Path(__file__).resolve().parents[1]
try:
    import tomllib
except ImportError:
    tomllib = None


class ConfigurationError(ValueError):
    """Messages are deliberately free of submitted or stored credential values."""


def field(data, name, required=True):
    value = data.get(name, '')
    if not isinstance(value, str) or len(value) > 8192 or any(c in value for c in '\r\n\x00'):
        raise ConfigurationError(f'{name} 格式无效；请使用单行文本')
    value = value.strip()
    if required and (not value or value.startswith('<') or value == '在本机填写'):
        raise ConfigurationError(f'请填写 {name}')
    return value


def encode_json(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def merge_mcp(original, token):
    if tomllib is None:
        raise ConfigurationError('自动接入 MCP 需要 Python 3.11+；可取消接入并先保存配置片段')
    try:
        before = tomllib.loads(original)
        expected = deepcopy(before)
        target = expected.setdefault('mcp_servers', {}).setdefault('seoagent', {})
        if 'command' in target or 'args' in target:
            raise ConfigurationError('已有 seoagent 使用本地命令传输，已保留原配置；请取消自动接入，先保存片段并核对迁移方式')
        target.update(enabled=True, url='https://www.seoagent.vip/mcp')
        target.setdefault('http_headers', {})['Authorization'] = 'Bearer ' + token
        updates = {
            'mcp_servers.seoagent': {'enabled': 'true', 'url': '"https://www.seoagent.vip/mcp"'},
            'mcp_servers.seoagent.http_headers': {'Authorization': json.dumps('Bearer ' + token)},
        }
        # Preserve all unrelated lines, including comments; unsupported TOML shapes fail validation.
        text = original
        for section, values in updates.items():
            header = re.compile(r'(?m)^\[' + re.escape(section) + r'\][ \t]*(?:#[^\n]*)?$')
            match = header.search(text)
            if match:
                following = re.search(r'(?m)^\s*\[', text[match.end():])
                end = match.end() + following.start() if following else len(text)
                block = text[match.end():end]
                for key, value in values.items():
                    pattern = re.compile(r'(?m)^[ \t]*' + re.escape(key) + r'[ \t]*=[^\n]*$')
                    if pattern.search(block):
                        block = pattern.sub(lambda m: f'{key} = {value}', block)
                    else:
                        block = block.rstrip('\n') + f'\n{key} = {value}\n'
                text = text[:match.end()] + block.rstrip('\n') + '\n\n' + text[end:]
            else:
                text = text.rstrip('\n') + f'\n\n[{section}]\n'
                text += ''.join(f'{key} = {value}\n' for key, value in values.items())
        if tomllib.loads(text) != expected:
            raise ValueError('unsupported shape')
        return text
    except ConfigurationError:
        raise
    except (ValueError, TypeError, AttributeError):
        raise ConfigurationError('现有 Codex TOML 结构无法安全合并；原文件保留，请改用配置片段') from None


class ConfigurationStore:
    def __init__(self, workspace, codex_home):
        self.workspace = Path(workspace).expanduser().resolve()
        self.codex_home = Path(codex_home).expanduser().resolve()
        if self.workspace == PACKAGE or PACKAGE in self.workspace.parents:
            raise ConfigurationError('客户工作区必须位于 Skill 安装目录之外')

    def path(self, relative):
        target = self.workspace / relative
        self.check_path(target, self.workspace)
        return target

    @staticmethod
    def check_path(target, root):
        if '..' in target.parts:
            raise ConfigurationError('配置路径不能包含上级目录跳转')
        try:
            target.relative_to(root)
        except ValueError:
            raise ConfigurationError('配置目标超出指定目录') from None
        for component in (target, *target.parents):
            if component == root:
                break
            if component.is_symlink():
                raise ConfigurationError('配置目标包含符号链接，已停止保存')
            if component.exists() and component != target and not component.is_dir():
                raise ConfigurationError('配置父路径不是目录')
        if target.exists() and not target.is_file():
            raise ConfigurationError('配置目标不是普通文件')

    def save(self, group, data):
        if not isinstance(data, dict) or any(k in data and not isinstance(data[k], bool) for k in ('replace', 'integrate')):
            raise ConfigurationError('提交格式无效')
        try:
            files = self.prepare(group, data)
            return self.commit(files, data.get('replace', False))
        except ConfigurationError:
            raise
        except (ValueError, TypeError, AttributeError, OSError, configparser.Error):
            raise ConfigurationError('保存停止，请检查本机配置格式与目录权限；未输出任何密钥') from None

    def prepare(self, group, data):
        if group == 'dataforseo':
            path = self.path('private/dataforseo.env')
            previous = load_env_file(path) if path.exists() else {}
            for key, form in [('DATAFORSEO_LOGIN', 'login'), ('DATAFORSEO_PASSWORD', 'password')]:
                previous[key] = field(data, form, False) or previous.get(key, '')
                field({form: previous[key]}, form)
                if any(c in previous[key] for c in "\"'"):
                    raise ConfigurationError('API 凭据不能包含引号；当前采集器不支持此格式')
            return {path: ''.join(f'{k}={v}\n' for k, v in previous.items())}
        if group == 'google_credentials':
            raw = data.get('google_json', '')
            if not isinstance(raw, str) or not raw:
                raise ConfigurationError('请选择 Google 下载的完整服务账号 JSON 文件')
            try:
                credential = json.loads(raw)
            except ValueError:
                raise ConfigurationError('Google JSON 无法解析') from None
            if (not isinstance(credential, dict) or credential.get('type') != 'service_account'
                    or not all(isinstance(credential.get(k), str) and credential[k].strip()
                               for k in ('client_email', 'private_key', 'project_id', 'token_uri'))
                    or '@' not in credential['client_email']
                    or not credential['private_key'].startswith('-----BEGIN PRIVATE KEY-----')
                    or credential['token_uri'] != 'https://oauth2.googleapis.com/token'):
                raise ConfigurationError('请选择完整 Google 服务账号 JSON，不能使用 API Key 或空白模板')
            return {self.path('private/google-service-account.json'): encode_json(credential)}
        if group == 'seoagent':
            token = field(data, 'token')
            fragment = merge_mcp('', token) if tomllib else (
                '[mcp_servers.seoagent]\nenabled = true\nurl = "https://www.seoagent.vip/mcp"\n\n'
                '[mcp_servers.seoagent.http_headers]\nAuthorization = ' + json.dumps('Bearer ' + token) + '\n')
            files = {self.path('private/seoagent-mcp.toml'): fragment}
            if data.get('integrate'):
                config = self.codex_home / 'config.toml'
                self.check_path(config, self.codex_home)
                original = config.read_text(encoding='utf-8') if config.exists() else ''
                files[config] = merge_mcp(original, token)
            return files
        if group == 'oss':
            env_path = self.path('private/oss.env')
            settings = load_env_file(env_path) if env_path.exists() else {}
            for key, form, default in (
                ('OSSUTIL_BIN', 'ossutil_bin', 'ossutil'), ('OSSUTIL_CONFIG_FILE', None, 'ossutilconfig'),
                ('OSS_BUCKET', None, 'jzyseo-reports'), ('OSS_PUBLIC_BASE_URL', None, 'https://reports.jzyseo.com'),
                ('OSS_REPORT_PREFIX', None, 'reports'), ('OSS_ARCHIVE_ROOT', 'archive_root', ''),
                ('GOOGLE_SOURCE_ARCHIVE_ROOT', 'source_root', ''),
            ):
                value = field(data, form, False) if form else ''
                settings[key] = value or settings.get(key) or default
                if (not settings[key] and key != 'OSS_ARCHIVE_ROOT') or any(c in settings[key] for c in '\r\n\x00\"\''):
                    raise ConfigurationError(f'请填写有效的 {form or key}，路径不加引号')
            ini_value = Path(settings['OSSUTIL_CONFIG_FILE']).expanduser()
            ini_path = ini_value if ini_value.is_absolute() else env_path.parent / ini_value
            self.check_path(ini_path, self.workspace)
            if not ini_path.is_relative_to(self.workspace / 'private'):
                raise ConfigurationError('OSS 密钥文件必须位于客户工作区 private/ 内')
            env_text = ''.join(f'{k}={v}\n' for k, v in settings.items())
            if not any(field(data, key, False) for key in ('access_key_id', 'access_key_secret', 'region')):
                return {env_path: env_text}
            ini = configparser.ConfigParser(interpolation=None)
            ini.optionxform = str
            if ini_path.exists():
                ini.read_string(ini_path.read_text(encoding='utf-8'))
            if not ini.has_section('default'):
                ini.add_section('default')
            for key, form in [('accessKeyID', 'access_key_id'), ('accessKeySecret', 'access_key_secret'), ('region', 'region')]:
                value = field(data, form, False) or ini.get('default', key, fallback='')
                field({form: value}, form)
                ini.set('default', key, value)
            output = io.StringIO()
            ini.write(output)
            return {env_path: env_text, ini_path: output.getvalue()}
        raise ConfigurationError('未知配置分组')

    def commit(self, files, replace):
        for path in files:
            root = self.workspace if path.is_relative_to(self.workspace) else self.codex_home
            self.check_path(path, root)
            if path.exists() and not replace and path != self.codex_home / 'config.toml':
                raise ConfigurationError('目标已有配置；如需更新请勾选“备份并更新已有文件”')
        ignore = self.path('.gitignore')
        ignored = ignore.read_text(encoding='utf-8') if ignore.exists() else ''
        if not any(line in ('private/', '/private/') for line in ignored.splitlines()):
            files[ignore] = ignored + ('\n' if ignored and not ignored.endswith('\n') else '') + 'private/\n'
        originals = {path: path.read_bytes() if path.exists() else None for path in files}
        backups, staged, written = [], {}, []
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
        try:
            for path, text in files.items():
                path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                if originals[path] is not None:
                    if path.is_relative_to(self.workspace):
                        backup = self.path('private/config-backups/' + stamp + '/' + path.relative_to(self.workspace).as_posix())
                    else:
                        backup = self.codex_home / 'seo-report-config-backups' / stamp / 'config.toml'
                        self.check_path(backup, self.codex_home)
                    backup.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    with backup.open('xb') as stream:
                        backup.chmod(0o600)
                        stream.write(originals[path])
                    backups.append(str(backup))
                fd, name = tempfile.mkstemp(prefix='.seo-config-', dir=path.parent)
                staged[path] = Path(name)
                with os.fdopen(fd, 'wb') as stream:
                    stream.write(text.encode('utf-8'))
                    stream.flush()
                    os.fsync(stream.fileno())
            for path, temporary in staged.items():
                # Recheck external edits immediately before replacement.
                current = path.read_bytes() if path.exists() else None
                if current != originals[path]:
                    raise ConfigurationError('配置在保存期间被其他程序修改，请刷新后重试')
                os.replace(temporary, path)
                written.append(path)
        except Exception:
            restore_failed = False
            for path in reversed(written):
                try:
                    if originals[path] is None:
                        path.unlink()
                    else:
                        fd, name = tempfile.mkstemp(prefix='.seo-restore-', dir=path.parent)
                        try:
                            with os.fdopen(fd, 'wb') as stream:
                                stream.write(originals[path])
                            os.replace(name, path)
                        finally:
                            Path(name).unlink(missing_ok=True)
                except OSError:
                    restore_failed = True
            if restore_failed:
                raise ConfigurationError('保存中断且自动恢复未全部完成。请保留本机 config-backups 备份并核对文件后恢复，不要继续提交') from None
            raise
        finally:
            for temporary in staged.values():
                temporary.unlink(missing_ok=True)
        return {'files': [str(p) for p in files if p != ignore], 'backups': backups,
                'message': '已保存到本机文件。服务连接、资源权限和发布尚未验证。'}

    def status(self):
        paths = ['private/google-service-account.json', 'private/dataforseo.env',
                 'private/seoagent-mcp.toml', 'private/oss.env', 'private/ossutilconfig']
        result = []
        for relative in paths:
            path = self.path(relative)
            result.append({'path': str(path), 'exists': path.is_file()})
        config = self.codex_home / 'config.toml'
        self.check_path(config, self.codex_home)
        return {'workspace': str(self.workspace), 'files': result, 'codex_config': str(config),
                'mcp_auto_merge': tomllib is not None,
                'google_env_override': bool(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')),
                'note': '文件存在不代表字段完整或服务已连接；密钥不会回显。'}
