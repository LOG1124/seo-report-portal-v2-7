#!/usr/bin/env python3
"""Create local empty configuration files without replacing existing files or calling APIs."""
from __future__ import annotations

import argparse
from pathlib import Path

from customer_registry import default_portal_slug

PACKAGE = Path(__file__).resolve().parents[1]
MACHINE_FILES = ('google-service-account.json', 'dataforseo.env', 'oss.env',
                 'ossutilconfig', 'seoagent-mcp.toml')
CUSTOMER_FILES = ('google-api.json', 'project-input.json', 'dataforseo-trial.json')


def setup_workspace(workspace: Path, domain: str | None = None) -> None:
    if domain is not None:
        default_portal_slug(domain)  # Reuse the registry's cross-platform domain validation.
        domain = domain.lower()
    workspace = Path(workspace).expanduser().resolve()
    if workspace == PACKAGE or PACKAGE in workspace.parents:
        raise ValueError('请使用 Skill 安装目录之外的客户工作区')
    destinations = [(name, workspace / 'private' / name) for name in MACHINE_FILES]
    if domain:
        destinations += [(name, workspace / 'private/customers' / domain / name)
                         for name in CUSTOMER_FILES]
    # Check all destinations before writing; never follow workspace-internal symlinks.
    for target in [path for _, path in destinations] + [workspace / '.gitignore']:
        for component in (target, *target.parents):
            if component == workspace:
                break
            if component.is_symlink():
                raise ValueError('配置目标包含符号链接，请先核对实际位置')
        if target.exists() and not target.is_file():
            raise ValueError('配置目标已存在且不是普通文件')
    for name, target in destinations:
        target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        try:
            with target.open('xb') as stream:
                target.chmod(0o600)
                stream.write((PACKAGE / 'configuration-templates' / name).read_bytes())
            print(f'已创建：{target}')
        except FileExistsError:
            print(f'保留已有文件：{target}')
    ignore = workspace / '.gitignore'
    existing = ignore.read_text(encoding='utf-8') if ignore.exists() else ''
    if 'private/' not in existing.splitlines() and '/private/' not in existing.splitlines():
        with ignore.open('a', encoding='utf-8') as stream:
            stream.write(('\n' if existing and not existing.endswith('\n') else '') + '\n# Local secrets\nprivate/\n')
    print('仅已创建/保留配置文件；尚未验证字段、Google 权限、MCP 连接、共享盘写权限或 OSS 发布。')
    print(f'逐项填写说明：{PACKAGE / "references/configuration-guide.md"}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--domain', help='已核实的客户规范域名；未知时先不建客户文件')
    args = parser.parse_args()
    try:
        setup_workspace(args.workspace, args.domain)
    except (ValueError, OSError) as exc:
        # Do not print exception payloads that might contain configured file contents.
        print(f'初始化停止（{type(exc).__name__}）：请核对域名、目标路径及本机权限。')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
