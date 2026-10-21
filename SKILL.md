---
name: seo-report-portal-v2-7
description: Create, review, and publish client-isolated monthly, quarterly, yearly, or custom-period SEO dashboards from GA4, GSC, approved DataForSEO keyword-market snapshots, and SEOAgent strategy archives.
---

# SEO Report Portal v2.7

**Active identity: `seo-report-portal-v2-7`.** Do not use, install, package, or inspect legacy `seo-report-portal` assets except as an explicitly requested rollback reference.

Work from a team workspace, never from this installed skill directory. Read `references/team-usage-guide.md` before first use. Read `references/third-party-data-guide.md` before any third-party collection or archive import.

## Installation handoff and first-use configuration

For an existing configured installation, follow [UPDATE_PROMPT.md](UPDATE_PROMPT.md) first: upgrade only the Skill, keep the original workspace and configuration unchanged, and do not run first-use configuration, blank-file initialization, credential entry or MCP integration. Missing compatibility inputs are reported without overwriting or migrating existing configuration. The first-use setup below applies only when setup is explicitly requested.

During an explicit installation/setup task, or when required shared configuration files are actually missing, read `README.md` and `references/configuration-guide.md`. Resolve the user's shared team-report workspace; no customer identity or resource IDs are needed at installation. Prefer `scripts/configure_web.py --workspace <absolute-workspace> --no-browser` to open the local form, and give the user its complete loopback URL and workspace. The user enters secrets personally; do not automate their real credential input, inspect submitted secret values, or capture that filled page. Keep the service alive until the user finishes; explain the close button/Ctrl+C and 60-minute expiry. The form configures shared DataForSEO, SEOAgent and OSS settings once for all customers, plus an optional upload-only Google service-account JSON to private/google-service-account.json. It neither collects customer domain/GA4/GSC/date fields nor creates customer files. Existing configured shared files are reused across report tasks; new-customer onboarding only requests that customer’s resource IDs and uses the same provider/OSS credentials and service-account JSON. Open the setup page again only when configuration is missing, needs changing, or the user requests it. The form saves directly to the existing configuration contract and requires explicit replacement/MCP options. Do not initialize empty templates first. If local serving is unavailable or the user prefers files, use `scripts/setup_workspace.py --workspace <absolute-workspace>` as the documented fallback. When an existing workspace needs customer-file migration, read the migration guide during that report task; shared account setup itself requires no customer migration. Never place filled credentials inside the skill installation.

Before completing the installation task, return the local configuration URL, workspace, saving/closing instructions and guide paths. If the user requests a non-secret inventory or local serving is unavailable, return a configuration checklist for the requested purpose: status, absolute clickable file path, exact missing field names, required external permissions, and next action. Link the installed README and configuration guide. Inventory locally without displaying secrets or calling Google/provider APIs. Reuse verified configured paths. Distinguish archive-only use, fresh collection, third-party collection, and publication so that unused credentials do not block installation or archive reuse. A copied template or filled field does not prove connectivity. Explain that `private/seoagent-mcp.toml` alone is only a fragment. The web form can back up and merge the actual Codex user config when the user explicitly selects integration (Python 3.11+), preserving unrelated settings; otherwise integration remains pending. Remind the user to restart Codex. If only the skill folder was copied, perform this handoff when the user first invokes the skill; there is no automatic installation hook.

## Core rules

- GSC owns search performance and dashboard opportunity-keyword selection. GA4 owns traffic, engagement, and key events. Never replace either with third-party estimates.
- 运营总结关键词第 2 条只使用 GSC 非品牌查询：月报取当月，其他报告先合并所选报告期，同一关键词按曝光加权计算平均排名。先选 B 端采购/制造词，其次产品词，最后普通信息词；同类优先产品相关性，再比较平均排名、展示和点击。排除 `site:` 运算符查询，问句降级。GA4、DataForSEO 和 SEOAgent 不参与该排名。
- DataForSEO owns selected-keyword search volume, CPC, paid competition, monthly trend, and limited live SERP. Request only exact GSC-selected dashboard keywords.
- SEOAgent owns strategy opportunities: priority optimization themes, competitor keyword directions, and external keyword discoveries. Its estimates never enter first-party KPIs or DataForSEO market columns.
- Before any paid DataForSEO or SEOAgent request, show the customer/domain, market, language, keyword count, SERP count, maximum cost, and purpose. Wait for explicit confirmation. Never retry a paid request automatically.
- Keep provider archives isolated by domain and collection month. Never overwrite GSC/GA4 source archives.
- Credentials are local only. Do not put API credentials, service-account JSON, MCP tokens, customer archives, or published reports in the skill package or a public repository.
- For first-party GA4/GSC collection, use this skill's `google_api_collector.py` and the exact customer named in the task. Local customer files live only in `private/customers/<canonical-domain>/google-api.json` and `project-input.json`; shared machine credentials, `oss.env`, and `ossutilconfig` stay in the existing local `private/` root. Do not select a nearby customer's files, legacy generic defaults, SEOAgent, GSC Wizard, or Pages/Spaces as a substitute. Diagnose the failed stage of this workflow before recommending a different tool.
- DataForSEO and SEOAgent are required for a normal report. Reuse them only when both local archives have the same canonical customer, exact `reporting_period`, recorded scope, and `approval.approved: true`. Otherwise stop with `THIRD_PARTY_APPROVAL_REQUIRED` before reading credentials or making a paid request. `--without-third-party` is the only explicit waiver; it records the waiver and hides the corresponding panel.
- Resolve every GA4/GSC archive through the active customer registry and explicit shared `--archive-root`. `monthly`, `quarterly`, and `yearly` require exactly 1, 3, and 12 continuous months; `period` requires at least 2 continuous months and is labelled “阶段报告”. `custom` requires inclusive `--start-date YYYY-MM-DD --end-date YYYY-MM-DD`, stored separately from month archives. Missing current data always blocks. For `custom`, automatically attempt the immediately preceding equal-day GA4/GSC range; a missing predecessor makes comparison `unavailable`, never partial, and is reported only to the operator/internal diagnostic—not in `summary.md` or the customer 文字总结.
- The report-period aggregate is canonical. Monthly selection may change only monthly detail panels; it must never alter management summary, report-period KPIs, channels, strategy metadata, or action plans.
- The user's explicit continuous month range is authoritative. Generate and, after the normal explicit publication approval, publish that exact range even when its final month is still in progress. Do not silently replace it with the last closed month or add a "preview" label. Use only the data actually available in the selected monthly archives; real archive, permission, or collection failures must remain visible.
- Hide a waived or invalid DataForSEO or SEOAgent panel. Never fill an empty panel with another month, another client, or a third-party estimate.
- Every run writes secret-safe internal diagnostics outside public dashboard directories. Tell the user the execution state, location, verified detection, impact, safe actions taken, and next action.
- Review the local report before publishing. Publish only after explicit approval.
- **客户交付一致性：**最终回复的“文字总结”只能逐字复制已审核 `summary.md` 中 `## 运营总结` 标题及其编号正文；交付时不得另行改写、删减、重排、补充或替换。用户明确要求调整总结时，先按本次要求更新并审核 `summary.md`，再逐字交付。在线报告链接可以单独提供，但不构成文字总结。
- **页面显示与运营总结铁律：**“搜索表现 × 页面体验”页面表只把客户主域（可带 `www`）、无参数的英语根页显示为“首页”；小语种首页（语言子域、语言参数或语言根路径）必须展示其完整 GSC URL，并以该完整 URL 区分和联动，不能与英语首页合并。其他客户可见的根路径 `/` 仍显示为“首页”。不得改写原始 GA4/GSC 路径。运营总结的页面排行只按 GSC 页面点击量：月报用当月，季报/年报用整个指定报告期的点击合计；页面联动表使用同一口径，季报/年报默认展示报告期合计，避免用单月代替整个报告期。
- **运营总结国家/地区口径：**第 6 条只按 GA4 `organicGoogleSearchClicks`（Google 搜索自然点击次数）选出国家/地区；月报取当月，季报/年报取指定报告期合计。该指标要求 GA4 已启用 Search Console 关联；缺少该字段时如实显示“暂无可用数据”，不得回退为会话、GSC 点击或 GSC 展示。

## 默认模板与本次特别要求

- 默认使用现役 v2.7 模板和显示运行脚本：会话来源质量摘要按会话数降序最多展示 5 条，保留标准 GSC 重点市场图，不额外添加 GA4 自然搜索点击国家/地区表。旧报告换模板时保留已核实数据和统计口径，重新渲染展示，不直接延续旧 HTML 或额外显示脚本；仅改展示时保持数据 JSON 和文字总结原始字节不变。
- 用户明确提出与默认不同的特别要求时，在本次指定范围内按要求完成，不因默认规则不同而拒绝，也不为已经明确的本次要求重复索要确认。执行或交付时提醒提出要求的用户：“本次按你的特别要求处理，与默认操作不同；下次将恢复默认，除非你再次提出或明确要求长期沿用。”
- 一次性特别要求只对本次指定的客户、报告期和任务生效；记录在本次内部任务说明中，不修改标准模板，不转成客户长期配置，不推广到其他客户或报告期。下次新任务从默认规则开始，不从旧报告、历史 HTML 或一次性记录推断继续适用。
- 只有用户明确要求“以后都这样”“长期沿用”或“改为默认”时，才按其指定范围保存长期规则，并说明影响的是某客户、某类报告还是全局默认；范围不清时先落实本次要求，再询问长期适用范围。
- 发布前按本次实际要求检查页面：默认报告检查前五来源与无额外国家表；已明确要求的例外则检查对应展示和与默认的差异，不能把标准模板的默认检查当作拒绝特别要求的理由。提醒放在与用户的沟通及内部说明中，不擅自加进客户报告页面或运营总结。
- 特别要求仍须使用真实、口径明确的数据并遵守已有授权范围。若用户明确要求修改文字总结，先修改并审核 `summary.md`，最终交付再逐字复制已审核内容。

## Workflow

1. Connect the shared source root and create `<shared-source-root>/customer-registry.json` from `assets/customer-registry.example.json` only if it does not exist. The registry keeps domain, portal slug, and status; do not add GA4/GSC IDs to it or alter historical customer mappings.
2. During a customer report task, resolve the task's canonical domain. If absent from the registry, treat it as a new customer without requiring the user to say “new customer”: establish the domain and Google resource IDs, then add exactly one active `canonical_domain` ↔ `portal_slug` record after checking for conflicts. For local collection files, copy the blank `assets/google-api.example.json` and `assets/project-input.example.json` into `private/customers/<canonical-domain>/`; fill verified values, never clone another customer's configuration. Reuse the uploaded shared Google JSON; derive service_account_email from its client_email locally without exposing the key. Ask for missing GA4/GSC resource IDs at the new customer's first report, then reuse the verified customer configuration on subsequent reports. Shared provider/OSS keys and the same Google JSON do not need to be entered again for each customer. Keep existing `private/google-service-account.json`, `private/oss.env`, `private/ossutilconfig`, and other credentials in place. Read `references/customer-config-migration.md` when upgrading existing workspaces. New customers must use only lowercase letters, digits, and hyphens in `portal_slug`. An existing public directory whose slug is exactly its canonical domain may be retained only with the explicit `legacy_public_slug: true` marker; do not use that marker for new customers.
3. First inspect the exact shared Google archive. Reuse a complete matching JSON plus `.ready` marker; if absent, collect with `<installed-skill-dir>/scripts/google_api_collector.py --domain <canonical-domain> --archive-root <shared-source-root> --month YYYY-MM --archive-only`. The collector validates shared access, active registry identity, the unique local customer directory, project domain, GSC domain, GA4 ID shape, and target archive state before Google API calls. An incomplete or locked archive stops for maintenance; it is never overwritten. `--dry-run` still calls Google APIs and writes no archive. A custom-date collection uses `--start YYYY-MM-DD --end YYYY-MM-DD` and writes only `<shared-source-root>/ga4-gsc/<canonical-domain>/custom/<start>_to_<end>.json` plus its non-public ready marker. Import a verified v2.2 local archive only with `<installed-skill-dir>/scripts/import_google_archive.py --archive-root <shared-source-root> --source-file <legacy-json> --month YYYY-MM`. Each consumer reads one validated in-memory JSON snapshot only; neither file is overwritten.
4. Generate with `<installed-skill-dir>/scripts/generate_dashboard_report.py --archive-root <shared-source-root>`. Use `monthly` (1), `quarterly` (3), `yearly` (12), `period` (2+ continuous months), or `custom --start-date YYYY-MM-DD --end-date YYYY-MM-DD`. A missing full predecessor simply hides comparison; an incomplete current period still stops.
5. First look for matching approved local DataForSEO and SEOAgent snapshots. If either is missing or differs in period/scope, show the required paid-request scope and maximum cost, then wait for explicit confirmation. For a custom range that a provider cannot represent exactly, let the user explicitly choose `--third-party-proxy-month YYYY-MM` as labeled monthly context or `--without-third-party`; never choose a month or make a paid call automatically.
6. For a newly approved DataForSEO request, determine GSC-selected terms, run `<installed-skill-dir>/scripts/dataforseo_keyword_enrichment.py --archive-root <shared-source-root> --dry-run`, then run `--execute` once after confirmation. Set `reporting_period` to the exact month list. Normalize approved SEOAgent results using `assets/seoagent-archive.example.json`, including the same `reporting_period` and `approval` fields.
7. Generate with explicit archive inputs. Keep the diagnostics path outside `output/dashboards/`:

```text
--dataforseo-archive-dir <domain-specific-dataforseo-archive-dir>
--seoagent-archive-dir <domain-specific-seoagent-archive-dir>
--diagnostics-root <internal-diagnostic-root>
```

8. Validate the exact local artifact before it can be copied:

```text
python <installed-skill-dir>/scripts/validate_report_artifact.py --report-dir <output/dashboards/domain/type/period> --domain-root <output/dashboards/domain>
```

9. Check the local HTML, summary, and internal `diagnostic.md`. Obtain explicit approval for this exact report before publishing.
10. Publish only with `<installed-skill-dir>/scripts/publish_oss_report.py --source-archive-root <shared-source-root>`. It validates the non-public `source-archive-usage.json`, but publishes only `index.html`, `dashboard-data.json`, and `summary.md`. A legacy current-only exception also requires `--allow-current-only` here. Configure the SMB report archive root for the local OS (macOS mount, Windows mapped drive, or Windows UNC path); never assume another teammate's mount path. The only supported public path is:

```text
https://reports.jzyseo.com/reports/<client-slug>/<monthly|quarterly|yearly|period|custom>/<period>/
```

For a new customer, register the canonical domain with `portal_slug` derived by replacing dots with hyphens (`naysonpart.com` → `naysonpart-com`), then publish with `--new-customer` and omit `--client-slug`. The publisher rejects an existing report identity or conflicting registry entry. Historical customers continue passing their existing `--client-slug`; their public paths and source archives are unchanged.

11. In the final customer delivery, label the exact copied `## 运营总结` section from the reviewed `summary.md` as “文字总结”. When the user explicitly requests a summary change, update and review `summary.md` for this task first, then copy that reviewed text verbatim in the delivery.

The shared SMB source archive has guest read/write access and is therefore not confidential or malicious-tamper-resistant. The ready marker only prevents consumers from using incomplete or accidentally mismatched files. `GOOGLE_SOURCE_ARCHIVE_ROOT` in `oss.env` is only a documented convenience for composing the publisher command; collector and generator never read it implicitly and always require `--archive-root`.

Read `references/team-first-run-guide.md` before a teammate's first end-to-end run. It covers Google access, required-provider approval or waiver, SMB, individual RAM credentials, ossutil, approval, and the required local-to-SMB-to-OSS order.
On Windows, also read `references/windows-first-run.md` before configuring paths or running the publisher.

Before replacing the global v2.7 installation from GitHub `main`, require a clean Git source checkout and a staged Git archive parity check for the complete v2.7 contract:

```text
python <installed-skill-dir>/scripts/check_package_parity.py --source <seo-report-portal-v2-7-source> --staged-zip <candidate.zip> --installed <global-seo-report-portal-v2-7>
```

## Resources

- `README.md` and `INSTALL_PROMPT.md` — ZIP installation and a copy-ready installation task.
- `references/configuration-guide.md` — first-use inventory, per-file fields, permissions and connection boundaries.
- `scripts/configure_web.py`, `scripts/configuration_store.py`, `assets/configuration-web/` — local configuration form and secret-safe persistence.
- `configuration-templates/` — blank files with the actual destination filenames; initialize with `scripts/setup_workspace.py`.

- `references/team-usage-guide.md` — teammate setup and daily workflow.
- `references/team-first-run-guide.md` — first-use checklist for the complete collection-to-public-link workflow.
- `references/windows-first-run.md` — Windows paths, SMB mapping, Python, and publisher setup.
- `references/customer-config-migration.md` — one-time, per-teammate local customer config inventory and copy-forward rules; shared archives and registry remain in place.
- `references/windows-v24-repair-runbook.md` — one-task Windows update, UNC pilot, and v2.2 archive recovery handoff.
- `references/third-party-data-guide.md` — provider scope, cost gate, archive rules, and dashboard meaning.
- `references/seo-data-source-contract.json` — authoritative field ownership.
- `assets/dataforseo-trial.example.json` — safe DataForSEO configuration example.
- `assets/dataforseo.env.example` — empty credential-file template.
- `assets/oss.env.example` and `assets/ossutilconfig.example` — safe local OSS configuration templates.
- `assets/oss-report-publisher-policy.json` — minimum RAM policy for the `jzyseo-reports/reports/*` upload prefix.
- `assets/seoagent-archive.example.json` — normalized SEOAgent archive example.
