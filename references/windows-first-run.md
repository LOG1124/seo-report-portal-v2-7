# Windows 首次配置

本说明仅适用于 Windows 工作区。不要运行 macOS 的 `chmod`、`/Volumes/共享盘` 或 `.venv/bin/python` 命令。

## 1. 本地工具与私密文件

在 PowerShell 的客户工作区执行。`$skill` 是 Codex 已安装的现役 v2.7 Skill。把 `$domain` 改为本次客户的已核实规范域名；安装 Skill 不会迁移旧客户配置，旧客户先按 `customer-config-migration.md` 逐个只读核对和复制：

```powershell
$skill = Join-Path $env:USERPROFILE '.codex\skills\seo-report-portal-v2-7'
$domain = 'example.com'
$customer = Join-Path 'private\customers' $domain
New-Item -ItemType Directory -Force $customer | Out-Null
if (-not (Test-Path 'private\dataforseo.env')) { Copy-Item "$skill\assets\dataforseo.env.example" 'private\dataforseo.env' }
if (-not (Test-Path 'private\oss.env')) { Copy-Item "$skill\assets\oss.env.example" 'private\oss.env' }
if (-not (Test-Path 'private\ossutilconfig')) { Copy-Item "$skill\assets\ossutilconfig.example" 'private\ossutilconfig' }
if (-not (Test-Path (Join-Path $customer 'google-api.json'))) { Copy-Item "$skill\assets\google-api.example.json" (Join-Path $customer 'google-api.json') }
if (-not (Test-Path (Join-Path $customer 'project-input.json'))) { Copy-Item "$skill\assets\project-input.example.json" (Join-Path $customer 'project-input.json') }
if (-not (Test-Path (Join-Path $customer 'dataforseo-trial.json'))) { Copy-Item "$skill\assets\dataforseo-trial.example.json" (Join-Path $customer 'dataforseo-trial.json') }
```

通过安全渠道手动放置 Google 服务账号 JSON 到 `private\google-service-account.json`，或保留已存在的本机文件。然后只在本机填写该客户的 `private\customers\<domain>\google-api.json`：从已核实的客户资料取得 GA4 资源 ID、GSC 的准确站点资源地址，并将示例 `service_account_email` 替换为该本地服务账号 JSON 的 `client_email`。不要把服务账号 JSON、真实账号信息或任何密钥粘贴到聊天、Skill 包或共享目录。设置了 `GOOGLE_APPLICATION_CREDENTIALS` 时，它会优先于配置中的 `credentials_file`；采集前核对实际使用的服务账号。

在该客户的 `private\customers\<domain>\project-input.json` 填写已核对的 `website_url`、`report_start`、`report_end` 和 `cooperation_level`。采集器、生成器和发布器始终从已安装的 `$skill\scripts\` 运行。新客户需先以该域名在共享注册表建立唯一 active 记录；不需要在任务文字中特地声明“新客户”。

上面的命令只在目标文件不存在时从空白示例创建，不覆盖已配置的同事凭据或客户文件。`dataforseo-trial.json` 也按客户放置，仅填写已批准的客户、月份和选词条件；这个试用配置不包含、也不能填写任何凭据，凭据仍在 `private\dataforseo.env`。

安装 Python 后，运行时优先使用 `.venv\Scripts\python.exe`；没有虚拟环境时使用 `py -3`。不要使用 macOS 路径 `.venv/bin/python`。

## 2. 连接 SMB 公盘

优先将公司 SMB 公盘映射为固定盘符，例如 `Z:`；也可使用 UNC 路径。共享盘为 guest 读写，故原始 GA4/GSC 档案**不是保密或抗恶意篡改的存储位置**。`.ready` 标记只用于拒绝半成品和意外不一致，不能防止可写者同时重写 JSON 与标记。首次路径预检只确认能打开指定根目录，不要用真实归档文件测试写入。

在 `private\oss.env` 中填写**一种**本机路径：

```dotenv
# 推荐：映射盘
OSS_ARCHIVE_ROOT=Z:\seo-report-portal

# 仅供复制到发布器 --source-archive-root；采集器和生成器不会隐式读取它。
GOOGLE_SOURCE_ARCHIVE_ROOT=Z:\seo-report-source-archive

# 或者：UNC
# OSS_ARCHIVE_ROOT=\\172.20.3.153\共享盘\seo-report-portal
# GOOGLE_SOURCE_ARCHIVE_ROOT=\\server\共享盘\seo-report-source-archive
```

不要填写 macOS 的 `/Volumes/共享盘/seo-report-portal`。SMB 用户名和密码由 Windows 凭据管理器处理，不能写入 `oss.env`。

## 3. OSS 配置与无写入验证

在 `private\ossutilconfig` 中填写该同事独立的 RAM AccessKey；在 `private\oss.env` 中指定 `ossutil.exe` 的实际路径或保持 `OSSUTIL_BIN=ossutil`（仅在它已加入 PATH 时）。不要把 AccessKey 贴入聊天。

Windows 必须直接使用 Python 发布器 `publish_oss_report.py`；`publish_oss_report.sh` 仅适用于 macOS。使用下列完整命令采集、生成和无写入发布：

```powershell
py -3 "$skill\scripts\google_api_collector.py" --domain example.com --archive-root 'Z:\seo-report-source-archive' --month 2026-08 --archive-only
py -3 "$skill\scripts\generate_dashboard_report.py" --type monthly --start-month 2026-08 --domain example.com --archive-root 'Z:\seo-report-source-archive' --output-root .\output\dashboards --diagnostics-root .\output\report-diagnostics --without-third-party
py -3 "$skill\scripts\dataforseo_keyword_enrichment.py" --config .\private\customers\example.com\dataforseo-trial.json --archive-root 'Z:\seo-report-source-archive' --credentials .\private\dataforseo.env --dry-run
py -3 "$skill\scripts\publish_oss_report.py" --local-report-dir .\output\dashboards\example.com\monthly\2026-08 --client-slug example-com --type monthly --period 2026-08 --oss-env .\private\oss.env --source-archive-root 'Z:\seo-report-source-archive' --dry-run
```

该发布示例用于历史客户。新客户先在共享注册表登记由真实域名生成的 slug，再把发布命令中的 `--client-slug example-com` 换成 `--new-customer`；发现已有客户报告时会停止。这里的 `--new-customer` 只表示首次发布，不是 Google 采集或客户配置选择开关。

补回已验证的 v2.2 本机原始档案时，使用导入器而不是手工复制共享盘文件：

```powershell
py -3 "$skill\scripts\import_google_archive.py" --archive-root 'Z:\seo-report-source-archive' --source-file 'C:\legacy\example.com\2026-07.json' --month 2026-07
```

导入只复制、不移动或删除本机旧 JSON，且不会覆盖已有目标。来源只能是旧版 GA4/GSC 原始 JSON，绝不能是 `dashboard-data.json`、`summary.md` 或 `index.html`。它会拒绝缺少 GA4、GSC、正确客户或自然月的文件；JSON 完整写入并同步后，才会独占写入同名非公开 `.json.ready` SHA-256 标记。报告、发布和自动选词只读取这两个文件均存在且哈希一致、存储周期恰为指定自然月的同一份内存快照。对 UNC，只把两处盘符路径替换为对应的单引号 UNC 路径。

如果命令提示某月份存在 `YYYY-MM.json.lock`，立即停止；它记录写入机器、进程与 UTC 开始时间。不要由普通同事删除锁，更不要删除、改名或手工补写目标 JSON 或 `.json.ready`。**只有指定维护负责人**在确认所有同事的采集/导入任务均已结束并已保存锁文件内容作为故障记录后，才可恢复：JSON 和 `.ready` 都存在时，先独立核对 `.ready` 的 SHA-256 与 JSON（导入时还须与本机源 JSON 相同）并记录结果，保留两者，随后才可移走遗留锁；只有 JSON 和 `.ready` 都不存在时，才可移走遗留锁并重试。只有其中一个文件存在或哈希不一致时是未就绪异常，任何工具都不会读取或覆盖它；保留现场并交给维护负责人处置，不能用资源管理器补写。

缺少完整上期时报告会如实标记对比不可用；不要使用部分上期数据。第三方快照缺失时，先确认新的付费范围和上限；只有用户明确不要第三方模块时才在生成命令中加 `--without-third-party`。对 UNC，不改变其它参数，仅把单引号内的 `Z:\seo-report-source-archive` 替换为 `'\\172.20.3.153\共享盘\seo-report-source-archive'`。

如果客户工作区已配置虚拟环境，也可把每条命令开头的 `py -3` 替换为以下 Python 运行器，其后的 `"$skill\scripts\..."` 和客户工作区参数不变：

```powershell
.\.venv\Scripts\python.exe
```

`--dry-run` 仅检查本地报告与 SMB 根路径，绝不写入 SMB、OSS 或线上链接。真实发布仍须先完成报告复核并取得本次报告的明确批准。

DataForSEO 的 `--dry-run` 也不访问付费接口；自动选词只会使用注册表中当前客户的完整共享 GA4/GSC 月档案。不要在配置中填写旧版 `source_archive` 本机路径；已确认的 `selected_keywords` 例外仍须通过同一客户注册表校验。
