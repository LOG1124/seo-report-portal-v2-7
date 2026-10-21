# 发给 Codex 的安装提示词

**已经配置好的同事请改用 [仅升级 Skill 的提示词](UPDATE_PROMPT.md)，不要执行下面的首次配置流程。**

把下面文字和此 ZIP 一起交给 Codex。只需确定本机共用的团队报告工作区；本次安装不用指定客户。

```text
请安装我附上的 seo-report-portal-v2-7 ZIP，按包内 README.md 启动一次性的本机共用配置网页。

核对 ZIP 是单一 seo-report-portal-v2-7 目录，包含 SKILL.md、README.md、assets/configuration-web/、scripts/configure_web.py 和空白模板；不含 private/、客户数据或实际凭据。解包拒绝绝对路径、.. 穿越及符号链接。安装此附件版本，不从 GitHub 覆盖。
使用实际 CODEX_HOME（未设置则 ~/.codex）的 skills/seo-report-portal-v2-7；仅替换同名 Skill。旧安装移到 skills 外的带时间戳备份目录；旧安装若包含 private/ 先停止替换并报告。保留其他 Skill、既有客户配置与共享档案。

确定我的团队报告工作区后运行 scripts/configure_web.py --workspace <工作区绝对路径> --no-browser，保持服务运行，交付终端给出的完整本机链接、工作区及保存/关闭方法。安装时不问客户域名、GA4/GSC ID 或报告日期。
网页只配置本机共用 DataForSEO、SEOAgent、阿里云 OSS/共享路径，后续所有客户复用。另有可选 Google 服务账号完整 JSON 上传入口：用户选择文件后，程序自动放到 private/google-service-account.json；不手填 Google 邮箱，不建立任何客户配置。
用户自己填写真实密钥和上传 JSON；不要通过聊天、截图或浏览器自动化收集这些真实值。已有配置默认保留，更新须由用户勾选备份更新；SEOAgent 接入真实 MCP 也须用户在网页勾选，保留其他设置。自动 MCP 合并需 Python 3.11+，旧版可先保存片段。
若共用配置已完成，告知可直接开始报告任务，不要求为每个客户重新配置。新客户首次生成报告时，按 Skill 工作流再核对该客户域名、GA4 资源 ID、GSC 站点资源和日期，使用已上传的共用服务账号，由你放置该客户配置；邮箱从本机 JSON 获取，不重复索取密钥。

如果本机网页不可用，说明具体原因，按 README 只建立机器级空白文件，逐项给出完整路径和填写位置；不要在安装阶段建立客户文件。
安装结束提供 README 与配置指南完整路径，提醒 MCP 接入后重启 Codex。安装/保存不等于服务已连接。
本次不调用 Google/第三方查询，不写共享档案，不发布报告。报告依赖缺失仅说明后续安装命令。
```

已安装后的简短入口：

```text
使用 $seo-report-portal-v2-7 为当前团队报告工作区打开本机共用配置网页。我只配置 DataForSEO、SEOAgent 和 OSS，并按需上传一次 Google 服务账号 JSON。客户资源留到新客户首次报告时再登记。
```
