#!/usr/bin/env python3
"""Publish an approved report through SMB and OSS on macOS or Windows."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Dict, Iterable
from urllib.request import urlopen

from customer_registry import default_portal_slug, require_active_customer
from report_periods import REPORT_TYPES, validate_report_label
from source_archive_usage import verify_usage


FILES = ("index.html", "dashboard-data.json", "summary.md")

def load_env_file(path: Path) -> Dict[str, str]:
    """Load simple KEY=VALUE settings without interpreting shell escapes."""
    values: Dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"私密配置第 {line_number} 行不是 KEY=VALUE 格式")
        key, value = line.split("=", 1)
        key = key.strip()
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*", key):
            raise ValueError(f"私密配置第 {line_number} 行的键名无效")
        values[key] = value.strip().strip('"').strip("'")
    return values


def resolve_config_path(value: str, base: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else base / path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def required_report_files(report_dir: Path) -> Iterable[Path]:
    for name in FILES:
        path = report_dir / name
        if not path.is_file():
            raise FileNotFoundError(f"本地报告产物不完整，缺少：{path}")
        yield path


def ossutil_command(value: str, base: Path) -> str:
    """Keep commands such as `ossutil` on PATH; resolve explicit local paths."""
    if any(separator in value for separator in ("/", "\\")) or value.startswith("."):
        return str(resolve_config_path(value, base))
    return value


def check_new_customer(record, source_root: Path, archive_root: Path) -> None:
    """Stop a first publication when this customer or public path already exists."""
    slug = default_portal_slug(record.canonical_domain)
    if record.legacy_public_slug or record.portal_slug != slug:
        raise ValueError(f"新客户须先登记域名生成的公开标识：{record.canonical_domain} → {slug}")
    customers = json.loads((source_root / "customer-registry.json").read_text(encoding="utf-8"))["customers"]
    if sum(item.get("canonical_domain", "").lower() == record.canonical_domain for item in customers) != 1:
        raise ValueError("该域名已有历史客户记录；请按历史客户流程发布")
    if any(item.get("portal_slug") == slug and item.get("canonical_domain", "").lower() != record.canonical_domain for item in customers):
        raise ValueError(f"公开标识已被其他客户登记：{slug}")
    if (archive_root / slug).exists():
        raise ValueError(f"共享盘已有公开标识目录：{slug}；请按历史客户流程发布")
    for data_path in archive_root.glob("*/*/*/dashboard-data.json"):
        old_payload = json.loads(data_path.read_text(encoding="utf-8"))
        old_domain = old_payload.get("report", {}).get("domain") if isinstance(old_payload, dict) else None
        if not isinstance(old_domain, str):
            raise ValueError(f"历史报告身份无法核对：{data_path}")
        if old_domain.lower() == record.canonical_domain:
            raise ValueError("共享盘已有该域名的报告；请按历史客户流程发布")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="审核后将 SEO 报告从 SMB 归档发布到 OSS")
    parser.add_argument("--local-report-dir", type=Path, required=True)
    parser.add_argument("--client-slug", help="历史客户必填原公开标识；新客户由真实域名生成")
    parser.add_argument("--new-customer", action="store_true", help="仅首次发布新客户时使用")
    parser.add_argument("--type", choices=sorted(REPORT_TYPES), required=True)
    parser.add_argument("--period", required=True)
    parser.add_argument("--oss-env", type=Path, default=Path(os.environ.get("OSS_ENV_FILE", "private/oss.env")))
    parser.add_argument("--source-archive-root", type=Path, required=True)
    parser.add_argument("--allow-current-only", action="store_true")
    parser.add_argument("--replace-archive", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.new_customer:
        if args.client_slug or args.replace_archive:
            raise ValueError("新客户首次发布不能指定 --client-slug 或 --replace-archive")
    elif not args.client_slug:
        raise ValueError("历史客户必须传入原 --client-slug；新客户须显式传入 --new-customer")
    validate_report_label(args.type, args.period)

    report_dir = args.local_report_dir.resolve()
    report_files = tuple(required_report_files(report_dir))
    try:
        report_domain = json.loads((report_dir / "dashboard-data.json").read_text(encoding="utf-8"))["report"]["domain"]
    except (KeyError, TypeError, json.JSONDecodeError) as exc:
        raise ValueError("dashboard-data.json 缺少报告域名") from exc
    source_root = args.source_archive_root.resolve()
    record = require_active_customer(source_root, report_domain)
    if args.new_customer:
        args.client_slug = default_portal_slug(record.canonical_domain)
    if record.portal_slug != args.client_slug:
        raise ValueError("客户标识与共享映射不一致")
    verify_usage(
        report_dir, source_root, record, args.type, args.period, args.allow_current_only
    )

    env_file = args.oss_env.resolve()
    if not env_file.is_file():
        raise FileNotFoundError(f"缺少私密配置：{env_file}；请复制 oss.env.example 并填写本机路径。")
    settings = load_env_file(env_file)
    archive_value = settings.get("OSS_ARCHIVE_ROOT", "")
    if not archive_value:
        raise ValueError("oss.env 缺少 OSS_ARCHIVE_ROOT；请填写 macOS 挂载路径、Windows 映射盘或 Windows UNC 路径。")
    archive_root = resolve_config_path(archive_value, env_file.parent)
    if not archive_root.is_dir():
        raise FileNotFoundError(f"SMB 归档根目录不存在或未连接：{archive_root}")
    if args.new_customer:
        check_new_customer(record, source_root, archive_root)

    config_value = settings.get("OSSUTIL_CONFIG_FILE", "ossutilconfig")
    ossutil_config = resolve_config_path(config_value, env_file.parent)
    ossutil = ossutil_command(settings.get("OSSUTIL_BIN", "ossutil"), env_file.parent)
    bucket = settings.get("OSS_BUCKET", "jzyseo-reports")
    public_base = settings.get("OSS_PUBLIC_BASE_URL", "https://reports.jzyseo.com").rstrip("/")
    prefix = settings.get("OSS_REPORT_PREFIX", "reports").strip("/")
    archive_dir = archive_root / args.client_slug / args.type / args.period
    remote_prefix = f"oss://{bucket}/{prefix}/{args.client_slug}/{args.type}/{args.period}"
    public_url = f"{public_base}/{prefix}/{args.client_slug}/{args.type}/{args.period}/"

    print(f"发布目标：{remote_prefix}/")
    print(f"公开链接：{public_url}")
    print(f"公盘归档：{archive_dir}")
    for path in report_files:
        print(f"{path.name:<22} {path.stat().st_size} bytes  {sha256(path)}")

    if args.dry_run:
        print("DRY_RUN：已验证本地报告和 SMB 路径；未写入 SMB、OSS 或线上链接。")
        return 0

    if not ossutil_config.is_file():
        raise FileNotFoundError(f"缺少 ossutil 私密配置：{ossutil_config}")
    if shutil.which(ossutil) is None and not Path(ossutil).is_file():
        raise FileNotFoundError(f"未找到 ossutil：{ossutil}")

    for source in report_files:
        destination = archive_dir / source.name
        if destination.is_file() and not args.replace_archive and sha256(source) != sha256(destination):
            raise FileExistsError(f"公盘已有不同版本：{destination}；如确认替换，请增加 --replace-archive。")

    archive_dir.mkdir(parents=True, exist_ok=True)
    for source in report_files:
        shutil.copy2(source, archive_dir / source.name)
    for source in report_files:
        if sha256(source) != sha256(archive_dir / source.name):
            raise RuntimeError(f"公盘归档校验失败：{source.name} SHA-256 不一致。")
    print("公盘归档完成，三份文件与本地版 SHA-256 一致。")

    for name in FILES:
        subprocess.run([ossutil, "cp", "-c", str(ossutil_config), str(archive_dir / name), f"{remote_prefix}/{name}", "--force"], check=True)

    with tempfile.TemporaryDirectory(prefix="oss-report-check-") as temporary:
        remote_file = Path(temporary) / "index.html"
        with urlopen(public_url, timeout=60) as response:  # nosec B310: approved public report URL
            remote_file.write_bytes(response.read())
        local_sha = sha256(archive_dir / "index.html")
        remote_sha = sha256(remote_file)
        if local_sha != remote_sha:
            raise RuntimeError("线上 index.html 校验失败：SHA-256 不一致。")
    print(f"上传成功，线上 index.html SHA-256 校验一致：{remote_sha}")
    print(f"客户交付链接：{public_url}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
        print(f"发布已停止：{error}", file=sys.stderr)
        raise SystemExit(1)
