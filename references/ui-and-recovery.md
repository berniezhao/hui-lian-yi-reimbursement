# UI Operations and Recovery

## One bounded business operation

Before interaction, identify the current state: reimbursement list, main form, report detail, expense drawer, upload dialog, selector/date picker, validation popup, or unknown/loading. Choose controls only inside the active state. Prefer fresh `snapshot -i` refs, then visible text and label-scoped DOM, then a verified coordinate target. For expenses, scope to the visible `.expense-form-box`; class names alone do not prove that an element is active.

For each control: locate → scroll into view → check visible, enabled and unobstructed → interact → wait for the expected condition. Expected conditions include a correctly titled dialog, a checked radio, updated field value, both date inputs and duration, or a saved line readback. A click returning success proves only transport success. Fixed sleeps may accompany a bounded condition wait but must not replace the condition.

Batch a deterministic business operation into one tool invocation when supported, such as selecting one cost center or saving and reading back one expense. Preserve checks after each internal action and exit immediately on an unexpected state; do not queue blind clicks or batch multiple expense creates. Snapshot again at changed-state boundaries instead of taking a full screenshot after every click. These are procedures, not preimplemented helper APIs.

## eval hygiene

- Wrap multi-statement `eval` scripts in a block `{ ... }`; top-level `const` re-declaration fails when a similar script runs again in the same page.
- Scope DOM queries to the visible `.expense-form-box` when a drawer is open, and filter candidates with `getClientRects().length` so hidden stale copies are excluded.

## Main-form selectors

1. Locate the field in the active form and `scrollIntoView({block:'center'})` it first. Out-of-viewport fields swallow ellipsis clicks: the click reports success but no dialog opens (verified 2026-09-14). Then click the right-side `...` icon, not the label/value container.
2. Wait for the dialog and verify its title matches the intended field. A click that opens the wrong dialog or an unrelated field means stale refs: close only the unintended selector (Escape where safe), re-snapshot, retry once with the corrected target. Repeated wrong-dialog behavior is a blocker, not a reason to keep clicking.
3. Enter the search keyword, click `搜 索`, and wait for results. Prefer narrowing the dialog list to a single matching row before selecting; this makes the selection deterministic.
4. Select the matching row/cell rather than the bare `radio` ref — direct radio clicks often leave `checked=false` with `确 定` disabled (verified 2026-09-14). Verify `checked=true` and that `确 定` becomes enabled before confirming.
5. Click `确 定`; wait for dialog closure and the intended field value to update.

Compact fields are inline dropdowns instead of modal selectors: `是否属于研发项目费用` is a 是/否 inline dropdown opened by clicking the field body. Do not hunt for an ellipsis there.

The v0.2.4 focus+Enter alternative for `.fake-input` fields did not open selectors in the 2026-09-14 run (发票抬头, cost centers). Scroll-then-ellipsis is the primary path; treat focus+Enter as unverified legacy.

## Ant control interaction primitives

Verified 2026-09-14/15 (agent-browser 0.22.3) on the HuiLianYi expense forms:

- **Date/range pickers** ignore plain `fill` and keyboard typing. Trigger with `mousedown` + `focus()` + `click()` on the input, then click the `gridcell` refs. A same-day range means clicking the same day cell twice. The adjacent disabled spinbutton (实际消费天数) recalculates automatically; verify it after picking.
- **City selectors**: OCR often pre-fills 出发/到达/城市 correctly. Read the field text first and skip re-selection when already correct. When selection is needed, `fill` on the in-dialog search box works, but commit the option with a full `mousedown`/`mouseup`/`click` sequence on the result item; a plain click closes the dropdown without committing.
- **React controlled inputs** (e.g. the subsidy amount): set the value through the native setter and dispatch synthetic events so React state updates:

  ```javascript
  const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  setter.call(input, '750.00');
  input.dispatchEvent(new Event('input', {bubbles:true}));
  input.dispatchEvent(new Event('change', {bubbles:true}));
  input.dispatchEvent(new KeyboardEvent('keyup', {bubbles:true, key:'Tab'}));
  ```

- **File uploads**: `agent-browser upload "input[type=file]" <path>` targets the first matching input, which is correct inside the single-input invoice dialog. Inside an expense form with multiple hidden inputs, first tag the target (`input.id = 'hly-attach-input'`) and upload via `#hly-attach-input`. Identify the input by its owning form-item label (see the DOM exploration snippet in [invoice-flows.md](invoice-flows.md)), never by index alone.

## Expense-line readback

- The expense list's `日期` column shows the creation date, not the business date (verified 2026-09-15: all six lines displayed 09-15 while business dates spanned 09-06~09-10). Never verify dates from the list.
- Open a saved line by dispatching `mousedown`+`mouseup`+`click` on the row's 序号 cell; clicking the 费用类型 cell is unreliable.
- Verify from the visible `.expense-form-box`: `input.value` for amount and dates, `innerText` for invoice number, attachment filename, cities and seat class.

## Login, QR code and proxy recovery

- Before requesting a QR code, inspect the current task session for an authenticated page (report list). When the user says login is complete, verify that state; do not request another QR without observing that login is still required.
- The QR page's in-page `重新获取` button may only clear the overlay without regenerating the code (verified 2026-09-14: QR pattern unchanged after click; the user's scan returned 无效的二维码). After any refresh attempt, compare the QR pattern with the previous screenshot; if identical, `open` the login URL again in a fresh session and re-capture. Record the capture time and never resend an old screenshot as fresh.
- `ERR_PROXY_CONNECTION_FAILED` means that browser session's proxy channel is stale; it is not evidence about the user's network. Open a new `agent-browser --session <new-name>` and continue there. Do not debug the old session's proxy or change global proxy settings.
- Distinguish three failure classes before recovering: website login expiry, QR expiry, and browser transport failure. Each has a different recovery path.
- Recover to the reimbursement list only after saving a safe checkpoint or acknowledging that unsaved form values may be lost. Verify the actual saved draft before resuming writes.

## Persistent checkpoints

Keep machine-maintained execution state locally in `.cache/runs/<trip-key>.json` (or an explicitly recorded writable task directory if the skill directory is not writable). Use a sanitized stable trip key, not a raw title as a path. Write atomically after each verified business save. Do not store cookies, authorization headers, raw HAR bodies or signed download URLs here.

Record:

- Source base/table/trip identity, schema discovery time and prepared main-form values.
- Source record roles, included business keys and exclusion reasons; date evidence and unresolved anomalies.
- Local invoice/support paths and SHA-256 values, without duplicating credentials or private attachment URLs.
- Report OID/ID/number and verified report status; each expense OID, invoice number, category, amount/currency, business dates and linked attachment IDs when available.
- Last verified state, pending action and unresolved differences.

Set an action to `pending` before a create that could be interrupted. If save times out, the drawer disappears without a readable identity, or the execution is interrupted, mark the result `unknown`, not failed or complete. Before any retry, read the draft/list and match invoice/document number, traveler, date, currency/amount and category against the prepared line. A unique match can be verified and adopted; multiple or unresolvable matches require stopping the create. Absence must be established from an adequately scoped live read, not a stale screenshot or checkpoint. There is no verified server-side idempotency key.

On resume, load the checkpoint, confirm authentication, then read the report and its current expenses. Reconcile actual state and pending/unknown actions before creating anything. A checkpoint records prior evidence; the live report is the authority for what exists now. Do not mark a line complete until readback confirms its business values and invoice/support associations. If structured readback is not available, reopen and verify via UI, recording any IDs or fields that remain unavailable.
