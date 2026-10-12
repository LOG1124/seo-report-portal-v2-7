# 旧客户本机配置整理

每位同事只整理自己当前工作区中的客户。此步骤不要求集中两台电脑的配置，也不修改共享盘的 `customer-registry.json`、`ga4-gsc/` 原始档案、OSS 报告或线上链接。共享注册表仍只记录 `canonical_domain`、`portal_slug` 和 `status`；不补录 43 个客户的 GA4/GSC 资源 ID。

1. **只读盘点。** 在当前工作区内找现有 Google 采集配置和项目配置；读取配置字段以建立候选配对：`project-input.json` 的 `website_url`、`google-api.json` 的 GA4 `property_id` 与 GSC `site_url`。只记录文件路径和非密钥的资源标识；不要打开、输出、复制或改写服务账号 JSON、AccessKey 或 Token。不要扫描整台电脑，也不要按相近公司名或文件名猜配对。
2. **核对一位客户。** 规范化 `www` 后，项目网站域名、GSC 资源域名与共享注册表活动域名必须相同。GA4 ID 必须从已批准的原配置或 Google 资源资料核实；服务账号能调用某个 GA4 ID 不足以证明该 ID 属于目标客户。旧客户的 `portal_slug` 保留原值。若有多套候选、缺字段、域名冲突或无法确认 GA4 归属，列出问题并停止该客户的迁移。
3. **只复制确定的本机文件。** 将已核对的 Google 配置与项目配置复制为 `private/customers/<canonical-domain>/google-api.json` 和 `project-input.json`；目标存在且内容不同即停止，不覆盖。检查 `credentials_file` 指向仍留在本机 `private/` 的服务账号；`GOOGLE_APPLICATION_CREDENTIALS` 若设置会优先于此字段，须核对它实际指向的账号身份。保留旧文件供回退；确保 `private/` 不进入公开 Git、Skill 包或同步目录。按客户使用的 DataForSEO 试用配置也放该客户目录，共用 `dataforseo.env`、`oss.env`、`ossutilconfig` 保留原位。
4. **按需验收。** 对已有完整 JSON 和 `.ready` 的月份，只用新 Skill 读取并核对客户、月份、摘要；不重新采集、不重生成或重发历史报告。客户没有本机采集配置但共享档案完整，仍可生成报告。缺少共享归档时，先完成该客户配置，再用 `google_api_collector.py --domain <domain> --archive-root <shared-root> --month YYYY-MM --archive-only` 首次采集。只有 JSON 或 `.ready` 之一存在、哈希不符或有锁时停止并保留现场。旧版原始 GA4/GSC JSON 只能通过 `import_google_archive.py` 验证后导入；`collected_data.json`、`dashboard-data.json` 和 `summary.md` 都不能冒充原始月档案。

若 Windows 共享路径报 `Access denied`，保留原错误、UNC 路径和执行身份，在普通 PowerShell 与 Codex 运行环境中检查同一路径。配置迁移可以先在本机完成，但共享档案验收和采集必须等路径恢复；不要改用 SEOAgent、GSC Wizard、Pages/Spaces 或第三方估算值填补 GA4/GSC。
