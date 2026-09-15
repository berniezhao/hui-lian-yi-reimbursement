# DingTalk Source Preparation

## Source Data

Primary source: DingTalk AI Table from config key `dingtalk_aitable.url`.

Discover and cache source metadata before querying records:

1. Parse `base_id` from the last path segment of the DingTalk AI Table URL.
2. Run `dws aitable base get --base-id <base_id> --format json` to verify access.
3. Run `dws aitable table get --base-id <base_id> --format json` to list tables (this does not return field schemas).
4. Identify the trip table and detail table by names/purpose, preferring `Trips` and `Trip Details` when present.
5. For each selected table, run `dws aitable field list --base-id <base_id> --table-id <table_id> --format json`, then build a field role map using the aliases below.
6. If a required role is missing or ambiguous, ask the user once, then cache the resolved table IDs and field role map in `.cache/discovered-source.json`.

Always read DingTalk data with `dws aitable ... --format json`. Do not scrape the DingTalk page.

```bash
dws aitable base get --base-id <base_id> --format json
dws aitable table get --base-id <base_id> --format json
dws aitable field list --base-id <base_id> --table-id <table_id> --format json
dws aitable record query --base-id <base_id> --table-id <trips_table_id> --query "<Trip ID or keyword>" --limit 10 --format json
dws aitable record query --base-id <base_id> --table-id <trip_details_table_id> --query "<Trip ID>" --limit 30 --format json
```

Record query responses use field IDs as keys; map them back to field names from `field list` before reasoning.

## Decoding dws JSON (verified 2026-09-14)

- `field list` items expose `fieldId`, `fieldName`, `type` — there is no `name` key. Build the `fieldId → fieldName` map once and reuse it for all record reads.
- `record list` / `record query` return `records[].cells` keyed by `fieldId`. Cell values are objects; decode by type:
  - `singleSelect` / `multipleSelect`: read `.name`
  - number / currency / text: `.value` is an array; take `.value[0]`
  - `attachment`: array of objects with `filename`, `url`, `resourceId`, etc.
- Date cells may include time/timezone; use the calendar date unless the form requires a time.

## Downloading attachments

- Attachment URLs are signed and short-lived: download during the same session as the query. Plain HTTPS GET with a browser User-Agent works.
- Derive the local filename from the source `filename` and keep its original extension — the HuiLianYi upload and OCR flows depend on it. Verify downloaded size > 0 before planning the expense line.

## Field role maps

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

## Normalize before UI entry

Classify each source record as an **expense voucher**, **support attachment**, or **excluded item** with a reason. A hotel invoice and matching order describe one expense, even when both source rows contain the same amount. Sum only included expense vouchers, then add calculated subsidy. Count source records, expense lines, and attachments separately; source-table totals are a cross-check, not the accounting authority. Rollup columns such as `总金额` can double-count support rows and mix currencies (observed 2026-09-14: a 4,039 rollup included a USD-158 hotel-order support row already covered by its CNY invoice). Compute the reimbursement total from the classified expense lines, never from the rollup.

Match invoice/support by traveler, category, route or merchant, actual business dates, document number and amount. File names alone and successful OCR/save do not establish a match. Preserve an exclusion such as a free return ride; do not invent a return expense or require a return invoice for it.

Reject impossible years or inconsistent date ranges before entry. Resolve from the original ticket/order and explicit user confirmation; record the evidence source and original anomalous value. Do not silently replace a year or convert a calendar date as if it were a timestamp. If evidence still conflicts, ask for the missing fact and continue independent preparation.

Create a prepared plan containing trip ID/dates/route, new or existing report identity, main-form values, and one row per expense with category, amount/currency, actual dates, invoice and support paths/hashes. Record excluded items and unresolved differences. Verify required files exist before opening a half-filled drawer. Do not begin affected entry while a required business field or support file is missing.
