---
name: hui-lian-yi-reimbursement
description: Operate HuiLianYi (汇联易) travel reimbursement drafts from DingTalk AI Table data. Use for reading the user's 钉钉多维表差旅报销助手, creating or editing 汇联易差旅费用报销 drafts, uploading travel invoices and support files, adding 机票/火车/住宿费/差旅补贴 lines, handling fragile HuiLianYi SPA selectors/date pickers/upload controls, and stopping before final submission. Trigger keywords: 汇联易, HuiLianYi, 报销, 填报销, 报销单, 差旅费用报销, 钉钉多维表, 发票生成费用, 手录费用, 差旅补贴, 机票, 登机牌, 酒店发票.
---

# HuiLianYi Reimbursement

Operate HuiLianYi travel reimbursement drafts from the user's DingTalk AI Table. HuiLianYi is a fragile SPA: prepare data first, perform one small verified UI action at a time, and never submit automatically.

## Non-Negotiables

- Never click `提交` unless the user explicitly asks to submit.
- Never discover source data while a HuiLianYi drawer/modal is half-filled.
- Complete and verify the main report form before adding expense details.
- Add one expense line at a time; verify after every save.
- Use invoice-driven `发票生成费用` for airfare/train/hotel when invoice material exists.
- Use hand-entry `手录费用` only for `差旅补贴`, unless the user explicitly asks otherwise.
- Treat `click` success as transport success only; verify the business state changed.
- If a validation popup appears, read the visible text. Confirm only when allowed by the user/rules.

## Source Data

Primary source: DingTalk AI Table `差旅报销助手`

URL: https://alidocs.dingtalk.com/i/nodes/2Amq4vjg89gPawDaIP64XbbbV3kdP0wQ

Known tables:

| Table | Purpose | Table ID |
|---|---|---|
| `Trips` | one row per business trip / reimbursement bundle | `aRHU9rr` |
| `Trip Details` | one row per voucher / expense detail | `wesjkCs` |

Always read DingTalk data with `dws aitable ... --format json`. Do not scrape the DingTalk page.

```bash
dws aitable base get --base-id 2Amq4vjg89gPawDaIP64XbbbV3kdP0wQ --format json
dws aitable table get --base-id 2Amq4vjg89gPawDaIP64XbbbV3kdP0wQ --table-ids aRHU9rr,wesjkCs --format json
dws aitable record query --base-id 2Amq4vjg89gPawDaIP64XbbbV3kdP0wQ --table-id aRHU9rr --query "<Trip ID or keyword>" --limit 10 --format json
dws aitable record query --base-id 2Amq4vjg89gPawDaIP64XbbbV3kdP0wQ --table-id wesjkCs --query "<Trip ID>" --limit 30 --format json
```

Record query responses use field IDs as keys; map them back to field names from `table get` before reasoning.

Important formats:
- `singleSelect`: use `.name`
- `attachment`: array with `filename`, `url`, `resourceId`, `resourceUrl`, etc.
- date cells may include time/timezone; use the calendar date unless the form requires a time.

Core `Trips` fields:

| DingTalk field | HuiLianYi use |
|---|---|
| `Trip ID` | link trip header to details |
| `标题` / `行程摘要` | context check |
| `出差人` | traveler check |
| `开始日期` / `结束日期` | trip range and subsidy range |
| `出发地` / `目的地` | route context |
| `总金额` / `机票金额` / `酒店金额` / `其他金额` | reconciliation |
| `凭证数量` / `缺失项` / `报销缺字段` / `报销准备状态` | readiness check |
| `报销状态` / `汇联易状态` / `报销单ID` | create vs continue decision |
| `报销建议事由` | preferred `事由` |

Core `Trip Details` fields:

| DingTalk field | HuiLianYi use |
|---|---|
| `凭证类型` | invoice/support type |
| `业务日期` | consumption date |
| `发票号` / `票号/单号` | duplicate/matching check |
| `乘机人/入住人` | traveler/guest check |
| `出发地` / `目的地` / `承运/商家` / `航班/车次` | transport matching |
| `金额` / `币种` | line amount |
| `入住日期` / `退房日期` / `酒店名称` | hotel line fields |
| `是否纳入报销` / `报销映射状态` / `报销项分类` | whether/how to create line |
| `原始附件` | source file to download/upload |

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

Common values:

| Field | Value/source |
|---|---|
| `事由` | DingTalk `报销建议事由` or concise trip reason |
| `发票抬头` | search `021`, choose `深圳卓正光锥科技有限公司-021` |
| `成本中心-一级` | `集团职能部门` |
| `成本中心-二级` | `软件研发部` |
| `成本中心-三级` | `软件研发部` |
| `是否属于研发项目费用` | `否` |
| `出差类型` | `其他（请在事由处说明）` |
| `出差范围` | derive from trip, e.g. `跨省、直辖市` |
| `收款方` | current user, verify visible value |

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

