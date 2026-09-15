# HuiLianYi API Evidence — HAR Observation and Live Reads

HAR evidence: user-supplied XHR HAR captured 2026-09-12, reviewed offline 2026-09-14. It covers one new draft and two invoice-driven expense creates, including a support attachment. The HAR review itself did not replay requests. These are private-web candidate contracts, not a public API specification or a verified minimal write sequence. Revalidate current session/configuration before using a read route. Keep writes on the known UI flow until the specific endpoint and dependencies are validated within the user's authorized task.

The sample does **not** establish existing-expense updates, manual subsidy, login recovery or final submission. It also contains mismatched business data (an aviation invoice assigned to hotel category, and a train date range unlike its ticket date); use it to understand structure, never as a source of correct expense values.

## Live authentication and read evidence (2026-09-14)

After a fresh QR login, `agent-browser` read the current page’s `localStorage` inside `eval`: `hly.token` is JSON with `access_token` and `token_type`; `hly.custom-browser-tenantId` is a decimal string. `Authorization: Bearer <access_token>`, `X-Tenant-Id: btoa(tenantString)` and `Accept: application/json` successfully read the current travel form: HTTP 200, 21 fields, matching form OID. The browser request used `credentials: omit` and `redirect: error`. Credentials never appeared in output or script files. See [browser-auth.md](browser-auth.md) for the verified probe and limitations.

Earlier live checks using the user-supplied credential also returned HTTP 200 for the form and custom-button list. Reading the old HAR report returned HTTP 400 with business error `129702` (“单据不存在”), including with page-context headers; this is not evidence of authentication failure. No create, upload, update, refresh-token or submit endpoint was live-validated.

## Observed request chain

| Purpose | Method and path | Evidence / follow-up |
|---|---|---|
| Main-form configuration | `GET /api/custom/forms/{formOID}` | Resolve current fields and dependencies dynamically |
| Company and cost-center options | `/api/widget/company/all/v2`, `/api/cost/center/item/children/...`, `/api/control/cascade/common/search` | Methods/payloads not specified here; use current account and hierarchy |
| Create draft | `POST /api/expense/reports/custom/form/draft` | Observed body had `submit:false`; response supplied identity |
| Read report | `GET /api/v3/expense/reports/{OID}` | Verify report identity, amount and report-level status |
| Upload invoice original and recognition image | `POST /api/upload/attachment` | Observed PDF + JPEG pairs; two uploads need not mean duplicate invoices |
| OCR | `POST /receipt/api/receipt/ocr/v3` | Observed request array: each item contains an `oriAttachment` object and a `picAttachment` array |
| Verify receipts | `POST /receipt/api/receipt/verify/batch` | Check business result, not only HTTP status |
| Expense types/configuration | `/api/expense/type/byUser`, `GET /api/expense/types/select/{id}` | Fetch allowed current types and complete configuration |
| Invoice defaults | `POST /invoice/api/invoice/defaults` | Defaults depend on current expense/invoice context |
| Amount and apportionment | `/invoice/api/receipt/cal/total_amount`, `/api/expense/default/apportionment` | Observed dependencies; optionality and methods not established here |
| Upload support | `POST /api/upload/attachment` | Returned OID was associated separately from the receipt |
| Create expense | `POST /invoice/api/v5/invoices` | Observed success response gave new OID, but several business fields were null |
| Read expenses | `GET /api/expense/report/invoices/v2` | Readback under `rows.invoiceViewDTOMap` contained full values and associations |

Dynamic form/type/user/org/company/receiver/report/expense/attachment IDs and query parameters must come from the current workflow. Do not hardcode values, cookies, tokens or temporary signed URLs from a HAR. This reference intentionally omits raw payloads and authentication data. No server idempotency guarantee was observed; result-unknown creates follow the read-before-retry procedure in `ui-and-recovery.md`.

## Dates: keep semantics separate

The sampled train and hotel expense-type configurations contained:

```json
{"showExpenseCreateDate":false,"occurDateDefaultValue":"CURRENT","dateLinkageValue":"none","notEditableDate":false}
```

This explains why searching repeatedly for an independent expense-date control can fail. Inspect current configuration first; do not reveal hidden controls or force undocumented payload values as a repair.

- Top-level `createdDate` was the capture day, independent of the trip range. The name alone does not establish its full business semantics or supported editability.
- UI evidence (2026-09-15): the expense list's “日期” column displays the creation date — all six lines of report ER36737582 showed 09-15 while their business dates spanned 09-06~09-10 and the reopened drawer inputs held the correct business dates. Which backend field (`createdDate` vs `createdDateWithTimeZone`) feeds the column is still unverified; a blank `tableColumns` config did not resolve it. Do not claim that changing `createdDate` fixes the list, and do not treat the column as a business-date check.
- `data[]` entry `fieldType: START_DATE_AND_END_DATE` stored a JSON string containing `startDate`, `endDate`, and `duration`. Those values persisted in readback. `duration` semantics are category-specific; hotel nights and subsidy inclusive days must not be conflated.
- Ticket travel date, hotel check-in/check-out, invoice issue date, expense occurrence date, creation timestamps and list display date need separate evidence/verification.
- Sample ranges used `timeZoneOffset:0` and Z-suffixed values including `23:59:59`. Preserve calendar-date intent; converting a range endpoint to Asia/Shanghai can spuriously create the next day. Convert true instants only when the field semantics call for it.

If actual trip dates are verified but another date remains unexplained, save that discrepancy in the checkpoint and report “草稿已保存，待核验”. Do not present it as fully correct.

## Attachments: combine requirement levels

The hotel field had `required:false` while the expense-type object had `isAttachmentRequired:true`, `attachmentRequired:1`, and prompt `请上传酒店订单截图或者账单`. Evaluate field rules, expense-type rules, company requirements and service validation together. A false field flag does not negate an explicit type requirement.

Invoice originals are linked through `receiptList`; support files are linked through top-level `attachments`. The support upload's OID equaled `attachments[].attachmentOID` on save and readback, even though the form's attachment `data[].value` was null. Verify the actual invoice/support associations after save, not just upload success or a thumbnail. Preserve one invoice per expense and match support to the correct traveler, merchant/route and dates.

## Amounts and states

- In the observed CNY samples, `receiptList[].totalAmount` used minor units (8200 for 82 yuan), while expense-level `amount` used yuan (82). Confirm units per field and currency; do not globally divide all monetary values by 100. Use exact decimal/minor-unit arithmetic when calculating totals.
- The server accepted mismatched invoice category and dates in the sample. It does not replace local business checks or voucher/support deduplication.
- Save returned `success:true` and `code:0000` with an OID, but `amount`, `businessCode` and `invoiceStatus` were partly null. Read the expense list/detail to accept business values, then checkpoint.
- Expense readback `invoiceStatus:SUBMITTED` coexisted with an unchanged report status (`1001` in this sample) and no final-submit request. Expense state is distinct from report submission. Establish report status through the current report object and UI; do not generalize the numeric enum from one sample.

## Remaining validation work

Future bounded captures can establish an existing-expense edit/save/readback and a manual subsidy save/readback. Do not capture final submission or modify a live expense solely to fill evidence gaps without authorization. No extra HAR is required to apply the UI, reconciliation and checkpoint rules already documented here.
