# SEO Report Portal v2.7 · 本机共用配置版

修订：2026-10-20。安装后只配置一次共用账号，所有客户复用；客户的 GA4/GSC 资源在该客户首次生成报告时另行核对和登记。

## 安装后只做这些事

1. 网页填写 **DataForSEO、SEOAgent、阿里云 OSS** 的共用账号和设置。
2. Google 服务账号无需手填邮箱或密钥字段：在可选上传入口选择 Google 下载的**完整 JSON**，程序自动放到 `private/google-service-account.json`。已有文件则不用重传。
3. 后续直接向 Codex 提出客户报告需求。新客户的域名、GA4 数字资源 ID、GSC 站点资源、报告日期等，由 Codex 在首次报告任务中核对并写入该客户配置；旧客户复用已经核实的配置。

网页不收集客户域名、GA4/GSC ID 或报告日期，也不会生成客户配置。使用者在同一个团队报告工作区下管理多个客户；共用凭据放在该工作区 `private/`，客户资源放在 `private/customers/<域名>/`。

## 已配置同事仅升级 Skill

已有配置的同事使用 [专用升级提示词](UPDATE_PROMPT.md)。从 GitHub 的 `main` 取得并固定提交，只替换 Skill 文件，完整备份旧 Skill；继续使用原团队工作区、原凭据、原 MCP 和原客户配置。此次升级不启动配置网页，不运行初始化或迁移，不修改原工作区文件。下面的首次安装流程不适用于这种纯升级。

## 最简单的安装方式

把此 ZIP 附给 Codex，并复制 [INSTALL_PROMPT.md](INSTALL_PROMPT.md) 的任务文字。Codex 安装后为指定的**团队报告工作区**启动共用配置网页，交付本机链接；不用先选客户。

没有自动安装钩子：仅解压不会弹出页面。使用安装提示词，或安装后发送“使用 $seo-report-portal-v2-7 打开本机共用配置网页”。

手动安装：ZIP 中 `seo-report-portal-v2-7` 整个目录放到下列位置，目录内直接有 `SKILL.md`。已有同名 Skill 先移到 Skill 目录之外的带时间戳备份目录。

- macOS/Linux：`~/.codex/skills/seo-report-portal-v2-7/`
- Windows：`%USERPROFILE%\.codex\skills\seo-report-portal-v2-7\`
- 设置 `CODEX_HOME` 时，用实际 `<CODEX_HOME>/skills/seo-report-portal-v2-7/`。

安装包自带空白模板，不含真实凭据或客户数据。团队报告工作区须在 Skill 安装目录之外；真实密钥不填回分发包。

## 打开一次性配置网页

在团队报告工作区执行：

macOS/Linux：

```bash
python3 ~/.codex/skills/seo-report-portal-v2-7/scripts/configure_web.py --workspace .
```

Windows PowerShell：

```powershell
$skill = Join-Path $env:USERPROFILE '.codex\skills\seo-report-portal-v2-7'
py -3 "$skill\scripts\configure_web.py" --workspace .
```

设置 `CODEX_HOME` 时替换 Skill 路径。程序默认打开浏览器；也可复制终端输出的完整 `http://127.0.0.1:<随机端口>/#<会话标识>`。Codex 启动时可加 `--no-browser` 并将完整链接交给用户。

页面分为三组共用服务配置，另外提供可选的 Google JSON 上传入口。每组单独保存，结果显示实际文件路径。已有文件默认保留；需要修改时勾选备份更新。DataForSEO/OSS 更新时密钥留空可保留原值。

SEOAgent 可勾选备份并接入实际 Codex MCP，保留其他设置；完成后重启 Codex。自动 MCP 合并需 Python 3.11+；网页其他功能支持 Python 3.9+，不需额外依赖。旧 Python 可以先保存 MCP 片段。

填写完成点击“关闭配置服务”，或终端 Ctrl+C；60 分钟后也会自动结束。网页只监听本机、不加载外部资源、不回显已有密钥、不主动写入浏览器存储。保存配置不会自动查询服务、授予权限或发布报告。

## 保存位置与作用范围

以下路径相对于同一个**团队报告工作区**，不是每个客户各存一套：

| 用途 | 共用文件 | 网页填写内容 |
| --- | --- | --- |
| DataForSEO | `private/dataforseo.env` | API Login / API Password |
| SEOAgent | `private/seoagent-mcp.toml`；可选择接入实际 Codex `config.toml` | Token |
| OSS 上传 | `private/ossutilconfig` | 本人 RAM AccessKey ID、Secret、地域 |
| 发布与共享路径 | `private/oss.env` | ossutil、本机报告归档根目录、Google 源档根目录 |
| Google 共用服务账号 | `private/google-service-account.json` | 只上传完整 JSON，自动放置 |

只生成本地报告时，可以只保存源档根目录，OSS 密钥和发布目录稍后补。更换电脑或团队工作区时需安全迁移/核对共用文件，不能假定另一目录会自动找到这些凭据。

备份在工作区 `private/config-backups/<时间戳>/`；Codex 用户配置备份在实际 `CODEX_HOME/seo-report-config-backups/<时间戳>/config.toml`。备份也含凭据，只留本机。恢复时按页面显示的备份路径在本机还原对应文件。

## 新客户首次报告时才准备的内容

用户提供报告需求后，Codex 核对客户真实域名、GA4 数字资源 ID、GSC 站点资源及报告期，再为这个客户创建/补齐：

```text
private/customers/<规范域名>/google-api.json
private/customers/<规范域名>/project-input.json
```

`credentials_file` 引用已上传的共用 Google JSON；服务账号邮箱由该 JSON 的 `client_email` 获取，无需用户重新手填。GA4/GSC 资源仍需管理员授权给该服务账号。已有完整共享档案的客户可直接复用，不强制补齐本机采集配置。

登记新客户及后续报告不需要重新打开共用配置网页，不重复索取三个服务的密钥，也不重新上传相同 Google JSON。付费数据每次仍须确认客户、范围和费用上限；每份报告仍需审核及明确发布批准。

详细字段和权限说明见 [配置指南](references/configuration-guide.md)，日常流程见 [团队指南](references/team-usage-guide.md)，旧配置整理见 [迁移指南](references/customer-config-migration.md)，Windows 路径见 [Windows 指南](references/windows-first-run.md)。

## 文件方式回退与运行环境

无法使用网页时，先建立机器级空白文件，**不要传客户域名**：

```bash
python3 <安装目录>/scripts/setup_workspace.py --workspace <团队报告工作区>
```

包内 `configuration-templates/` 提供同名空白文件，手填位置见配置指南；客户模板保留供 Codex 在首次报告任务中使用。初始化仅创建缺失文件，保留已有内容，并向工作区 `.gitignore` 补入 `private/`。已被 Git 跟踪的秘密不会因忽略规则自动停止跟踪。

网页和初始化只需 Python 标准库。实际生成/采集时，在团队报告工作区建 `.venv`，用其 Python 安装 Skill 的 `requirements.txt`：

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install -r <安装目录>/requirements.txt
```

Windows 使用 `py -3 -m venv .venv`，再执行 `.\.venv\Scripts\python.exe -m pip install -r <安装目录>\requirements.txt`。发布还需安装 ossutil 并连接共享盘。配置文件已保存只表示本机配置存在，资源权限和真实连接要另行验证。
