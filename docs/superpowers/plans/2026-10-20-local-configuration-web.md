# Local configuration web implementation plan

> Execution: implement natively in the current chat under the user's approved local-web workflow. No Git commit, global installation, real credentials or live API calls are part of this task.

**Goal:** Replace manual first-run file editing with a local form that saves the same configuration contract.
**Architecture:** A Python standard-library loopback HTTP server serves bundled HTML/CSS/JS. It writes only fixed workspace configuration targets and, when selected, the SEOAgent section of the actual Codex user config. Keep existing report scripts unchanged.
**Spec:** User-approved six-step configuration flow in this chat, 2026-10-20.

## Constraints and review focus

- Preserve existing files unless the user explicitly enables replacement; create private backups before replacement. Never echo existing credentials into HTML, HTTP responses, logs or browser storage.
- Bind 127.0.0.1 on a random port; require session token, matching Host and Origin for writes; limit request body. No external assets or queries. Close on user action or expiry.
- Workspace/domain are explicit; reject invalid domains, symlinks, path traversal and multiline env/INI values. Validate all group inputs before writing; restore prior files if a group fails midway.
- Existing MCP config may contain unrelated settings, comments and secrets. Parse the resulting TOML, compare intended semantic changes, and preserve unrelated lines; fail closed on unsupported shapes. Automatic TOML merge requires Python 3.11+, with fragment-only fallback on older Python.
- Saving proves local files only, not provider connectivity, fees, shared-disk rights or publication approval. Do not auto-register clients or write shared archives.

## Tasks

- [x] Add failing isolated tests for configuration output, preservation/backup, invalid inputs, symlinks, rollback, MCP semantic preservation and local HTTP authorization/secret-free responses.
- [x] Implement scripts/configure_web.py and scripts/configuration_store.py; use existing domain validation, config examples and credential-field names.
- [x] Add bundled assets/configuration-web/index.html, app.css and app.js: grouped forms, JSON file upload, password inputs, explicit replacement/MCP checkboxes, status/path results, close button and responsive layout.
- [x] Update README, installation prompt, Skill routing, configuration guide, changelog and canonical package parity.
- [x] Run focused and package tests; exercise upload/save/replacement in a temporary browser workspace. Inspect desktop/mobile screenshots, then build a new ZIP and independently unpack/test it. Keep earlier ZIPs.

Validation (2026-10-20): Python 3.12 129/129 pass; Python 3.9 129 tests pass with 2 automatic-TOML tests skipped by design. Browser test used temporary fake credentials only: Google upload, four groups, denied overwrite, backup update, MCP preservation, 1440px/375px checks, explicit shutdown and disk readback. Earlier ZIP remains intact. No live provider, Windows-host, real credentials or global-install changes.

Independent read-only review found a same-name legacy stdio MCP transport conflict; automatic merge now rejects command/args and leaves the original intact. Added synthetic regression coverage. Also injected rollback failures to confirm the UI reports incomplete recovery while retaining backups.

Scope correction from user (2026-10-20): the current UI is one-time shared provider/OSS setup only; Google has an optional shared-JSON upload. No customer domain, GA4/GSC resource ID, reporting dates or per-customer config writes are exposed in the UI. Customer resource setup remains in the first report task, reusing the shared service account. Earlier four-group browser evidence describes the prior revision and does not prove the corrected UI.

Corrected-scope validation: 129 tests pass on Python 3.12; Python 3.9 passes with 2 TOML-merge skips. Ego TaskSpace 20 verified exactly three shared-service tabs, zero customer inputs, standalone Google JSON upload, disk readback with no private/customers directory, and desktop/mobile layouts. Temporary browser service closed.
