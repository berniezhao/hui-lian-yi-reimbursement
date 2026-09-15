# HuiLianYi Failure Modes

Use this reference when the SPA behaves unexpectedly. For visibility, condition waits, stale-ref selectors, login/proxy diagnosis and interrupted-save recovery, use [ui-and-recovery.md](ui-and-recovery.md). Stop after one evidence-based retry of an unexpected action. For an unknown create result, read back before retrying; do not apply the UI retry rule to a blind create POST.

## Dialog Radio Unchecked / `确 定` Stays Disabled

Symptoms:

- Clicking a visible `radio` ref in a selector dialog reports success but `checked` stays `false`.
- `确 定` remains disabled after selecting.

Fix (verified 2026-09-14):

- Narrow the dialog list to a single row with the in-dialog search box first.
- Click the row/cell containing the option, not the bare `radio` ref.
- Verify `checked=true` before clicking `确 定`.
- See [ui-and-recovery.md](ui-and-recovery.md) main-form selectors.

## Expense List Shows an Unexpected Date

Symptoms:

- A saved line's `日期` in the expense list is today (or another non-trip date) although the line was planned with trip dates.

Fix:

- The list `日期` column shows the creation date, not the business date (UI-verified 2026-09-15).
- Open the line (序号 cell, full mouse-event sequence) and verify the business dates from the `.expense-form-box` inputs instead.
- See [ui-and-recovery.md](ui-and-recovery.md) expense-line readback.

## Main Form Edits Restricted After Details Exist

Symptoms:

- After at least one expense line is saved, clicking main `编 辑` may show:
  `部分字段在有明细数据的情况下不允许修改，请先删除或者退回明细费用数据再进行修改`
- Header fields are no longer safely editable without deleting/returning detail lines.

Fix:

- Finish and verify all main fields before creating expense lines.
- If a main field must be corrected later, do not delete details automatically; ask the user or use only a known-safe editable path after verification.

## Selector Popup Ref Drift / Duplicate Refs

Symptoms:

- Clicking visible option text affects an unrelated field.
- A ref that looked like a popup option points to a left menu item or stale element.
- Inline dropdown selections for cost center do not register.

Fix:

- Prefer right-side `...` modal selector.
- Choose row/radio and verify `checked=true`.
- Click `确 定`.
- Confirm main form visible value.

## Ant Range Picker Same-Day Collapse

Symptoms:

- `开始结束日期` cannot be set with `fill`.
- Native value setter does not update form state.
- Clicking one date leaves both inputs empty or collapses both dates to the same day.
- Date panel stays open and field value does not match planned trip range.

Fix:

- Use the visual Ant calendar.
- Clear wrong values with `close-circle`.
- Click start once, then end once.
- Verify both inputs and day count.

## Wrong Save Button Container

Symptoms:

- Save click succeeds but form does not close.
- System exception codes appear.
- No visible change after save.

Root cause:

- Multiple `保 存` buttons can exist.
- A hidden/older `.slide-frame` button may be stale.
- The active expense drawer save is inside `.expense-form-box`.

Fix:

```javascript
const formBox = document.querySelector('.expense-form-box');
Array.from(formBox.querySelectorAll('button')).map((b, i) => ({ i, text: b.innerText }));
```

Click the save button inside the active form box. Do not click global buttons when identical labels exist.

## Coordinate Clicks on List Rows

Symptoms:

- jumps to homepage
- opens wrong page
- fails to open detail page

Fix:

- run `snapshot -i`
- click report-number cell by ref
- never click the left `+` when the goal is opening a report

## Screenshot Reading Drift

Symptoms:

- describing fields not visible
- carrying context from previous screenshots

Fix:

- state only what is visible now
- distinguish visible / not visible / inferred
- if a detail panel is blank or absent, say so

## Wrong Attachment Type

Symptoms:

- airfare item still invalid after invoice upload
- message says electronic-ticket/boarding-pass attachment missing

Fix:

- attach the matching boarding pass, not the invoice PDF
- invoice upload and required support attachment are separate targets

## Hidden Upload Input Mismatch

Symptoms:

- uploaded file appears somewhere, but validation still says attachment missing

Fix:

- identify all `input[type=file]`
- associate each input with its parent form item label and nearby text
- upload to the input owned by the specific required `附件` field
- re-check validation after upload

## Upload Success Is Not Line Ready

Symptoms:

- system shows `识别成功` / uploaded invoice count
- final save still fails on required fields such as dates, amount, seat class, or attachment

Fix:

- after OCR success, still verify every required field before save
- treat final save validation as the source of truth

## Popup Handling

Symptoms:

- `检查结果`
- `超费用标准`

Fix:

- Read the exact validation message and determine whether it requests a business-rule override.
- Existing explicit authorization to continue that override remains valid; do not ask again.
- If the override is not authorized, pause the affected save and ask; ordinary informational confirmation can proceed within the draft task.

