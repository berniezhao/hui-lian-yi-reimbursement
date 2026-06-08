---
name: hui-lian-yi-reimbursement
version: "0.2.3"
description: "Operate HuiLianYi (汇联易) travel reimbursement drafts from DingTalk AI Table data. Use for reading the user's 钉钉多维表差旅报销助手, creating or editing 汇联易差旅费用报销 drafts, uploading travel invoices and support files, adding 机票/火车/住宿费/差旅补贴 lines, handling fragile HuiLianYi SPA selectors/date pickers/upload controls, and stopping before final submission. Trigger keywords: 汇联易, HuiLianYi, 报销, 填报销, 报销单, 差旅费用报销, 钉钉多维表, 发票生成费用, 手录费用, 差旅补贴, 机票, 登机牌, 酒店发票."
---

# HuiLianYi Reimbursement

Operate HuiLianYi travel reimbursement drafts from the user's DingTalk AI Table. HuiLianYi is a fragile SPA: prepare data first, perform one small verified UI action at a time, and never submit automatically.

Skill version: `0.2.3`. When updating this skill, increment the frontmatter `version` with SemVer: patch for wording or small workflow corrections, minor for backward-compatible capabilities, major for breaking workflow or schema changes.

## Non-Negotiables

- Never click `提交` unless the user explicitly asks to submit.
- Never discover source data while a HuiLianYi drawer/modal is half-filled.
- Complete and verify the main report form before adding expense details.
- Add one expense line at a time; verify after every save.
- Use invoice-driven `发票生成费用` for airfare/train/hotel when invoice material exists.
- Use hand-entry `手录费用` only for `差旅补贴`, unless the user explicitly asks otherwise.
- Treat `click` success as transport success only; verify the business state changed.
- If a validation popup appears, read the visible text. Confirm only when allowed by the user/rules.

## Prerequisites

Before reading DingTalk data, verify that the `dws` CLI is available:

```bash
which dws
```

If the command is not found, ask the user:

> `dws` CLI 未安装，需要从 https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli 安装才能读取钉钉数据。是否现在安装？

Only proceed if the user agrees. Then check whether GitHub is reachable:

```bash
curl -s --max-time 5 https://raw.githubusercontent.com > /dev/null && echo reachable || echo unreachable
```

**GitHub reachable** — install via the official script:

```bash
curl -fsSL https://raw.githubusercontent.com/DingTalk-Real-AI/dingtalk-workspace-cli/main/scripts/install.sh | sh
```

**GitHub unreachable** — fall back to npm (npm registry is usually accessible without a proxy):

```bash
npm install -g dingtalk-workspace-cli
```

If npm also fails, tell the user:

> `dws` 安装失败，GitHub 和 npm 均无法访问。请您开启代理后重试，或手动从 https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli/releases 下载对应平台的二进制文件并放入 PATH。

Do not proceed with the task until `which dws` succeeds.

## Configuration

Use `config.local.yaml` if present. Otherwise use `config.example.yaml` as the template and ask the user before assuming personalized defaults.

If no usable DingTalk AI Table URL is configured, tell the user to open the table template below, create their own copy, then paste the new table URL into `config.local.yaml` under `dingtalk_aitable.url`:

https://alidocs.dingtalk.com/i/nodes/P7QG4Yx2Jp7ePkDPCgBNyEnEV9dEq3XD?corpId=ding1eff7bf4d86437eb35c2f4657eb6378f&iframeQuery=applicationId%3DKY9tlWg5NEHgfs8WT6IO2%26entrance%3Ddata

Human-maintained config should contain only:

- DingTalk AI Table URL
- HuiLianYi main report defaults such as invoice title, cost centers, R&D flag, travel type, travel scope default, and payment receiver strategy

Do not move stable company rules into config:

- HuiLianYi URL and browser flow
- expense type mapping
- subsidy standards
- attachment rules
- file matching rules
- safety rules such as never clicking final `提交`

Local discovery/cache files belong under `.cache/` and are machine-maintained.

## Source Data

Primary source: DingTalk AI Table from config key `dingtalk_aitable.url`.

Discover and cache source metadata before querying records:

1. Parse `base_id` from the last path segment of the DingTalk AI Table URL.
2. Run `dws aitable base get --base-id <base_id> --format json` to verify access.
3. Run `dws aitable table get --base-id <base_id> --format json` to list tables and fields.
4. Identify the trip table and detail table by names/purpose, preferring `Trips` and `Trip Details` when present.
5. Build a field role map from table schemas by matching field names and aliases below.
6. If a required role is missing or ambiguous, ask the user once, then cache the resolved table IDs and field role map in `.cache/discovered-source.json`.

Always read DingTalk data with `dws aitable ... --format json`. Do not scrape the DingTalk page.

```bash
dws aitable base get --base-id <base_id> --format json
dws aitable table get --base-id <base_id> --format json
dws aitable record query --base-id <base_id> --table-id <trips_table_id> --query "<Trip ID or keyword>" --limit 10 --format json
dws aitable record query --base-id <base_id> --table-id <trip_details_table_id> --query "<Trip ID>" --limit 30 --format json
```

Record query responses use field IDs as keys; map them back to field names from `table get` before reasoning.

Important formats:
- `singleSelect`: use `.name`
- `attachment`: array with `filename`, `url`, `resourceId`, `resourceUrl`, etc.
- date cells may include time/timezone; use the calendar date unless the form requires a time.

Core `Trips` field roles and aliases:

| Role | Preferred aliases | HuiLianYi use |
|---|---|---|
| `trip_id` | `Trip ID`, `行程ID` | link trip header to details |
| `title` | `标题`, `行程摘要` | context check |
| `traveler` | `出差人` | traveler check |
| `start_date` / `end_date` | `开始日期` / `结束日期` | trip range and subsidy range |
| `origin` / `destination` | `出发地` / `目的地` | route context |
| `amounts` | `总金额`, `机票金额`, `酒店金额`, `其他金额` | reconciliation |
| `readiness` | `凭证数量`, `缺失项`, `报销缺字段`, `报销准备状态` | readiness check |
| `report_status` / `report_id` | `报销状态`, `汇联易状态`, `报销单ID` | create vs continue decision |
| `reason` | `报销建议事由` | preferred `事由` |

Core `Trip Details` field roles and aliases:

| Role | Preferred aliases | HuiLianYi use |
|---|---|---|
| `voucher_type` | `凭证类型` | invoice/support type |
| `business_date` | `业务日期` | consumption date |
| `document_no` | `发票号`, `票号/单号` | duplicate/matching check |
| `person` | `乘机人/入住人`, `乘机人`, `入住人` | traveler/guest check |
| `route_vendor_no` | `出发地`, `目的地`, `承运/商家`, `航班/车次` | transport matching |
| `amount` / `currency` | `金额` / `币种` | line amount |
| `hotel_fields` | `入住日期`, `退房日期`, `酒店名称` | hotel line fields |
| `reimbursement_mapping` | `是否纳入报销`, `报销映射状态`, `报销项分类` | whether/how to create line |
| `attachments` | `原始附件` | source file to download/upload |

Before opening HuiLianYi, create a short plan:

```text
Trip: <Trip ID, title, dates, route>
Report: <new or existing ER...>
Main form: <reason, scope, cost centers>
Lines:
- <category, date/range, amount, invoice file, support file>
Missing/Risky:
- <anything needing user confirmation>
```

Do not start UI entry if core fields or required files are missing.

## HuiLianYi Entry

Use the active `agent-browser` session. Prefer a named session such as:

```bash
agent-browser --session hly open "https://console-a2.huilianyi.com/main/expense-parent-report/expense-report"
```

If login is required, switch to QR code login, send the screenshot, and wait for the user.

Stay in `工作台` and the left menu `报销单`. Do not enter unrelated modules.

### Open or Create a Draft

For an existing draft:

1. open the reimbursement list
2. `agent-browser --session hly snapshot -i`
3. click the report-number cell by ref, not row coordinates or the left `+`
4. verify the detail page actually opened

For a new draft:

1. open the reimbursement list
2. click `新建报销单`
3. re-snapshot after the menu appears
4. click `差旅费用报销`
5. fill and verify the main form before creating details

## Main Form

Common values come from `report_defaults` in config:

| Field | Value/source |
|---|---|
| `事由` | DingTalk `报销建议事由` or concise trip reason. For a new report, append a new final line: `（本报销单由Codex协助填写）` |
| `发票抬头` | search `report_defaults.invoice_title_search`, choose `report_defaults.invoice_title` |
| `成本中心-一级` | `report_defaults.cost_center_1` |
| `成本中心-二级` | `report_defaults.cost_center_2` |
| `成本中心-三级` | `report_defaults.cost_center_3` |
| `是否属于研发项目费用` | `report_defaults.is_r_and_d_project` |
| `出差类型` | `report_defaults.travel_type` |
| `出差范围` | derive from trip; fall back to `report_defaults.travel_scope_default` |
| `收款方` | `report_defaults.payment_receiver`, usually `current_user` |

Selector fields with a right-side `...` are more stable through the modal selector than inline dropdowns:

1. click the field's right-side `...`
2. wait for a dialog titled with the field name
3. select the row or history chip
4. verify the radio/row is checked
5. click `确 定`
6. re-snapshot and confirm the main form shows the value

Avoid duplicate/stale refs in dropdowns. If a normal ref click behaves oddly, use the modal title, row text, and radio state as the source of truth.

After saving/validating the main form, re-read visible text and confirm all required fields. Once expense lines exist, main-form edits can be restricted; do not delete details automatically to fix header data.

## SPA State Machine

Before every action, classify the visible state:

| State | Action |
|---|---|
| list page | open by report-number-cell ref, or create new report |
| main report form | fill/verify header fields, then save or proceed |
| report detail page | choose `发票生成费用` or `手录费用` for the next planned line |
| expense edit drawer | complete exactly one line, then save |
| upload dialog | upload exactly the intended file to the intended input |
| date picker / selector modal | finish selection and verify affected field |
| validation popup | read text; confirm only if allowed |
| unknown/loading | wait briefly, snapshot again, or recover to a stable anchor |

Stable anchors:
- reimbursement list URL
- report number cell
- visible report number / status
- drawer title: `新建费用`, `编辑费用`, `差旅费用报销`
- visible validation messages
- line count / amount total
- labels: `发票生成费用`, `手录费用`, `附件`, `事由说明`

Interaction priority:

1. `agent-browser snapshot -i` ref
2. visible text plus scoped DOM query
3. label-scoped DOM query inside the active drawer/form
4. hidden file input only after identifying the owning form item
5. coordinate click only for a verified target when no ref/DOM path works

When using DOM/JS, scope to the active UI. Prefer `.expense-form-box` for the current expense drawer and avoid global buttons when identical buttons exist elsewhere.

## Component Recipes

Read [references/invoice-flows.md](references/invoice-flows.md) when adding airfare/train/hotel/subsidy lines or handling uploads/date pickers.

Quick routing:

| Line type | Preferred path |
|---|---|
| `机票` | `发票生成费用`, upload one airfare invoice, then upload matching boarding pass as required attachment |
| `火车` | `发票生成费用`, upload one train invoice/ticket material |
| `住宿费` | `发票生成费用`, upload hotel invoice, then required hotel bill/order/screenshot |
| `差旅补贴` | `手录费用` -> `差旅补贴` |

Attachment matching:
- airfare invoice matches boarding pass by flight number, route, date, and traveler
- hotel invoice matches bill/order/screenshot by hotel name and stay dates
- keep invoice files and support files separate even if they belong to the same segment
- one invoice per expense line

For subsidy:
- 省内: RMB 100/day
- 跨省（含直辖市、港澳台）: RMB 150/day
- 国外: RMB 300/day
- `发生日期` should be an actual consumption/trip date, not today's default
- `开始结束日期` should be actual trip start/end; verify day count before saving

## Verification Checkpoints

After every component click:

1. wait briefly
2. snapshot or read the affected field
3. verify the value, selected row, checked radio, date range, line count, or drawer state changed

After every save:

1. wait briefly
2. snapshot
3. confirm one of: drawer closed, new/updated line visible, validation error visible, popup visible

If nothing changed, do not repeat the same click. Re-identify the active UI and correct button.

After adding lines, reconcile visible HuiLianYi totals/counts against DingTalk:

- included detail record count
- line categories
- visible category/total amounts
- missing attachments or validation errors

## Failure Handling

Read [references/failure-modes.md](references/failure-modes.md) when a UI action behaves unexpectedly, validation fails, uploads do not attach, dates collapse, or old/stale refs appear.

If a step fails:

1. state the exact failed step
2. state what is actually visible now
3. state whether the expected popup/dropdown/form appeared
4. retry once with a more deterministic method
5. stop instead of looping on the same failed action

Minimal user update style:
- good: `我现在看到 ER... 单号 cell ref 是 e28，我只点它。`
- bad: `应该已经进入详情页了，所以接下来...`
