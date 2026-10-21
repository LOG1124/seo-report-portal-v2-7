# 共用账号配置与新客户资源登记

## 安装时：只配置一次共用服务

使用 [README 的本机网页](../README.md)：`configure_web.py --workspace <团队报告工作区>`。本次不选择客户，也不填写 GA4/GSC 资源或报告日期。

| 内容 | 网页操作 | 自动保存位置（相对于团队报告工作区） |
| --- | --- | --- |
| DataForSEO | 填 API Login / API Password | `private/dataforseo.env` |
| SEOAgent | 填 Token；可选择接入 Codex MCP | `private/seoagent-mcp.toml` 及用户明确选择的实际 Codex 配置 |
| 阿里云 OSS | 填本人 RAM 密钥、地域、ossutil 和共用路径 | `private/ossutilconfig`、`private/oss.env` |
| Google 共用服务账号 | 在可选上传入口选完整 JSON | `private/google-service-account.json` |

这些文件供同一团队报告工作区的所有客户复用。已有文件无需重填/重传；网页默认保留，需要更换时勾选备份更新。不同电脑或工作区之间不自动复制密钥。

Google JSON 上传后，程序直接放置完整文件，不需要用户手填服务账号邮箱，不建立客户目录。服务账号的 `client_email` 在后续客户任务中由 Codex 从该文件取得；JSON 内容不输出到聊天。已有本机文件保持原样，换账号前应核对哪些客户引用它。

用户亲自在网页输入真实密钥或选择 JSON，Agent 不读取表单真实内容、不截图保存填写过程，也不将值转写到聊天。网页只显示保存路径及备份路径，密钥不回显。保存并不证明服务权限或连接成功。

## DataForSEO 填什么

填写管理员安全发放的 **API Login / API Password**，不要把网页登录密码当 API Password。实际对应字段：

```dotenv
DATAFORSEO_LOGIN=
DATAFORSEO_PASSWORD=
```

管理员需准备可用 API 权限和余额。已配置账号后，各客户复用同一文件；每次付费采集仍需确认域名、市场、语言、关键词数量、SERP 数和费用上限，失败不自动重试。

每个客户的 `dataforseo-trial.json` 是范围与预算配置，不是密钥文件；由 Codex 在具体报告任务中按已确认范围准备。已有匹配且经批准快照可以复用。不得重复配置第三方去替代 GA4/GSC。

## SEOAgent 填什么

只填管理员提供的 Token，不加 `Bearer` 前缀；程序生成正确配置片段。

勾选“同时接入 Codex MCP”时，程序先备份，再只合并实际用户配置的 SEOAgent 同名设置，保留其他内容。生效位置：

- macOS/Linux：`~/.codex/config.toml`
- Windows：`%USERPROFILE%\.codex\config.toml`
- 设置 `CODEX_HOME` 时：`<CODEX_HOME>/config.toml`

自动合并需要 Python 3.11+。旧 Python 可先保存片段；仅保存 `private/seoagent-mcp.toml` 不会加载。已有同名旧本地命令传输（stdio）或不支持的 TOML 结构时，程序保留原文件并提示改用片段核对迁移，避免破坏旧服务。

接入后重启 Codex，先检查 MCP 是否加载；不能用付费查询测试连接。模板沿用团队既有接入格式；若管理员更换服务地址/认证契约，先核对真实要求。

## OSS 和共用路径填什么

`private/ossutilconfig` 对应：

```ini
[default]
accessKeyID=<本人RAM_AccessKey_ID>
accessKeySecret=<本人RAM_AccessKey_Secret>
region=<实际Bucket地域>
```

使用本人最小权限 RAM 用户。团队现有策略参考 `assets/oss-report-publisher-policy.json`，仅允许目标报告前缀上传。网页适配既有 `jzyseo-reports` / `https://reports.jzyseo.com/reports/...` 门户，更换发布门户不是只换密钥即可完成的操作。

`private/oss.env` 对应：

| 字段 | 填写方式 |
| --- | --- |
| `OSSUTIL_BIN` | PATH 中的 `ossutil` 或本机可执行文件完整路径 |
| `OSSUTIL_CONFIG_FILE` | 默认同目录 `ossutilconfig`；保留已核实的本机配置位置 |
| `OSS_ARCHIVE_ROOT` | 所有客户共用的 SMB **报告归档根目录** |
| `GOOGLE_SOURCE_ARCHIVE_ROOT` | 所有客户共用的 **Google 源档根目录**，只记录位置 |

网页填写根目录，不用为每个客户填一条路径；客户子目录由现有报告流程处理。Windows 示例 `Z:\seo-report-portal` / `Z:\seo-report-source-archive`；macOS 示例 `/Volumes/共享盘/seo-report-portal` / `/Volumes/共享盘/seo-report-source-archive`。以本机真实路径为准，不在 env 内多加反斜杠转义或包裹引号。

仅做本地报告时，可只保存 Google 源档根目录，先不填写 OSS 密钥和报告归档目录。采集/生成仍显式传 `--archive-root`，发布仍显式传 `--source-archive-root`；程序不会隐式读取记录字段。安装时不写共享注册表；需要登记新客户时再按 Skill 的报告流程检查冲突并新增本次一条记录，不覆盖旧映射。

管理员还需准备 ossutil、共享盘访问与上传权限。共享登录由操作系统处理，不写入网页或 env。只读可访问不等于可写；不用真实历史档案试写，密钥不放共享盘。

## 新客户首次报告时：再核对 GA4/GSC

用户提出“给某客户生成某期报告”后，Codex 执行：

1. 确定规范域名、报告范围和客户身份，先查共享注册表及匹配 ready 档案。
2. 如需本机采集，核对该客户 GA4 **数字资源 ID**（不是 `G-...`）和 GSC 准确站点资源（`sc-domain:example.com` 或 URL 资源），缺失时向用户询问这些非秘密信息。
3. 创建/补齐 `private/customers/<域名>/google-api.json` 和 `project-input.json`。Google 配置引用已有共用 JSON，邮箱从其 `client_email` 获取；客户的 ID、站点和日期不复用另一客户的配置。
4. 管理员将目标 GA4/GSC 资源授权给共用服务账号。只读权限和真实资源归属必须核对；Google Cloud 项目应已启用 Google Analytics Data API 和 Search Console API。
5. 后续报告复用已核实的客户配置及共用账号；日期与报告范围按当次任务处理。

客户文件字段参考：

| 文件 | 字段 |
| --- | --- |
| `google-api.json` | `credentials_file` 指向共用 JSON；`service_account_email` 取其邮箱；`ga4.property_id`、`gsc.site_url` 属于该客户 |
| `project-input.json` | `website_url`、`report_start`、`report_end`、`cooperation_level`；无人工数据时 `manual_data` 保持 `{}` |

设置了 `GOOGLE_APPLICATION_CREDENTIALS` 时它优先于文件路径，需核对实际凭据身份。GA4 的 Search Console 关联是“Google 搜索自然点击次数”字段的前提，缺少时如实显示暂无数据。完整共享档案可直接复用时，无需为了生成报告补齐本机采集配置。

## 保存、备份与离线核对

网页 Python 3.9+、仅本机回环监听、无外部资源、按组保存；60 分钟到期，可点关闭或 Ctrl+C。正常保存失败会尝试恢复本组已写文件；恢复不完整会明确报告，需保留备份并在本机核对。网页拒绝符号链接目标与凭据写出团队工作区，已有特殊路径先按迁移指南核对。

工作区备份在 `private/config-backups/<时间戳>/`，Codex 备份在实际 `CODEX_HOME/seo-report-config-backups/<时间戳>/config.toml`。备份也有凭据，不分发。Agent 如需协助离线核对，只报告用途、文件完整路径、缺失字段、状态与下一步，不输出值、配置 diff 或原始异常。

安装验收只盘点共用配置，不索取客户域名/ID；新客户报告任务才盘点客户资源。不能把模板存在、字段填写或文件保存表述为 Google/MCP/SMB/OSS 已验证，更不能自动扣费或发布。
