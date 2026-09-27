---
name: hui-lian-yi-reimbursement
version: "0.5.2"
description: "Create and edit HuiLianYi (汇联易) travel reimbursement drafts from DingTalk AI Table records, including invoice-driven expenses, support attachments and travel subsidy. Use for 汇联易差旅报销填报、核对与恢复；stop before final submission unless explicitly requested."
---

# HuiLianYi Reimbursement

Prepare a verified reimbursement plan, complete the report header, then save and read back one expense at a time. This skill contains UI procedures, HAR-observed API contracts and a live-verified browser authentication probe. The probe performs one read-only form request; API writes remain unverified.

## Operating boundaries

- Never click final `提交` unless the user explicitly asks to submit. Draft creation is not authorization to submit.
- Prepare source records and required files before UI entry; do not discover source data with a half-filled drawer/modal.
- Finish, save and verify the main form before adding details. Do not delete details automatically to unlock header editing.
- Use `发票生成费用` for airfare/train/hotel when invoice material exists. Use `手录费用` only for `差旅补贴`, unless the user explicitly asks otherwise.
- Work on one expense at a time. An upload, OCR result, click or HTTP success is not proof of a correct saved expense.
- Read validation text. Existing user authorization persists; pause only if continuing would require an unauthorized override.
- Separate invoice amounts from support materials; never count an order and its invoice twice.
- A result-unknown create must be read back and checked for duplicates before retrying. No server idempotency guarantee has been verified.

## Prerequisites

Before reading DingTalk data, verify that the `dws` CLI is available:

- macOS / Linux: `which dws`
- Windows: `where dws`

If the command is not found, ask the user:

> `dws` CLI 未安装，需要从 https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli 安装才能读取钉钉数据。是否现在安装？

Only proceed if the user agrees. Then detect the OS and check whether GitHub is reachable:

**macOS / Linux — check GitHub:**

```bash
curl -s --max-time 5 https://raw.githubusercontent.com > /dev/null && echo reachable || echo unreachable
```

- Reachable → `curl -fsSL https://raw.githubusercontent.com/DingTalk-Real-AI/dingtalk-workspace-cli/main/scripts/install.sh | sh`
- Unreachable → `npm install -g dingtalk-workspace-cli`

**Windows — check GitHub (PowerShell):**

```powershell
try { Invoke-WebRequest https://raw.githubusercontent.com -TimeoutSec 5 -UseBasicParsing | Out-Null; "reachable" } catch { "unreachable" }
```

- Reachable → `irm https://raw.githubusercontent.com/DingTalk-Real-AI/dingtalk-workspace-cli/main/scripts/install.ps1 | iex`
- Unreachable → `npm install -g dingtalk-workspace-cli`

If npm also fails on any platform, tell the user:

> `dws` 安装失败，GitHub 和 npm 均无法访问。请您开启代理后重试，或手动从 https://github.com/DingTalk-Real-AI/dingtalk-workspace-cli/releases 下载对应平台的二进制文件并放入 PATH。

Do not proceed with the task until `dws` is found in PATH.

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

## Prepare and resume

Read [references/source-data.md](references/source-data.md) to discover table/field IDs, normalize evidence, calculate the proposed lines and resolve abnormal dates. `table get` lists tables; fetch schemas with `field list`. Always use `dws aitable ... --format json`, not DingTalk page scraping.

Read [references/ui-and-recovery.md](references/ui-and-recovery.md) before browser entry or resuming an interrupted task. It defines visible-state checks, selector procedures, Ant control interaction primitives (date/city pickers, React inputs, file-input targeting), expense-line readback, QR/proxy recovery and persistent checkpoints. On resume, reconcile the checkpoint against the live draft before any create operation.

For authenticated structured reads, use [references/browser-auth.md](references/browser-auth.md) and its probe. Acquire credentials inside the current HuiLianYi page; never ask the user to paste a fixed token or export browser state. A successful probe validates that form read only.

Use the active `agent-browser` session; prefer a dedicated named session:

```bash
agent-browser --session hly open "https://console-a2.huilianyi.com/main/expense-parent-report/expense-report"
```

Stay in `工作台` → `报销单`. Open an existing draft by its report-number cell with fresh refs. For a new draft use `新建报销单` → re-snapshot → `差旅费用报销`; verify the main form appeared. If login is required, use the QR recovery procedure and wait for the user.

## Main Form

Common values come from `report_defaults` in config:

| Field | Value/source |
|---|---|
| `事由` | DingTalk `报销建议事由` or concise trip reason. For a new report, append a new final line: `（本报销单由<agent>协助填写）`, where `<agent>` comes from the signature resolution below |
| `发票抬头` | search `report_defaults.invoice_title_search`, choose `report_defaults.invoice_title` |
| `成本中心-一级` | `report_defaults.cost_center_1` |
| `成本中心-二级` | `report_defaults.cost_center_2` |
| `成本中心-三级` | `report_defaults.cost_center_3` |
| `是否属于研发项目费用` | `report_defaults.is_r_and_d_project` |
| `出差类型` | `report_defaults.travel_type` |
| `出差范围` | derive from trip; fall back to `report_defaults.travel_scope_default` |
| `收款方` | `report_defaults.payment_receiver`, usually `current_user` |

### Signature name

Resolve `<agent>` in this order; never guess it from self-knowledge, because several agents' environment variables can coexist in one session:

1. `report_defaults.agent_signature` in config, if set.
2. Otherwise run `python3 scripts/detect-agent.py` and use its output.
3. The script already falls back to `AI助手`, so there is no third case to handle.

Use the modal selector procedure in [references/ui-and-recovery.md](references/ui-and-recovery.md). Verify and save every required header field, then record the draft identity and saved header checkpoint before creating expenses.

## Add and verify expenses

Read [references/invoice-flows.md](references/invoice-flows.md) for the current category and upload/date-picker procedure. Company subsidy rules remain 100 RMB/day for 省内, 150 RMB/day for 跨省（含直辖市、港澳台）, and 300 RMB/day for 国外. Use actual trip dates and verify subsidy day count.

When date controls are absent, attachment requirements conflict, or structured readback is available, read [references/api-contract.md](references/api-contract.md). Inspect the current form and expense-type configuration; do not hardcode sample IDs or force hidden fields. A list-date binding and existing-expense update API have not been established.

Save one line, read it back, and verify category, amount/currency, actual dates, traveler and invoice/support associations. Use the UI readback unless an authenticated read route has been validated in the current environment. Partial save responses provide identity only. Persist the verified checkpoint before the next line.

## Finish or diagnose

Reconcile expense-line count, category amounts, total and attachments against the prepared plan, including subsidy and excluded items. Read the report's own status and UI label: an expense `invoiceStatus: SUBMITTED` is not proof that the whole report was submitted. Do not invent a universal mapping for numeric report status.

Report the saved report number, amount, completion state and any unresolved date/attachment discrepancies. If a discrepancy remains, say “草稿已保存，待核验”; do not claim complete verification.

For unexpected UI/validation failures, use [references/failure-modes.md](references/failure-modes.md). Inspect the actual state, retry once by a more deterministic method, then stop the affected action instead of repeating clicks or writes. Communicate business milestones and concrete blockers, rather than each low-level click.

## Maintaining this skill

Increment the YAML `version` using SemVer and update `package.json` to match. `build.sh` validates both versions before packaging; local configuration, caches and credentials must not enter the distributable.
