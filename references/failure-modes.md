# HuiLianYi Failure Modes

Use this reference when the SPA behaves unexpectedly. Prefer visible evidence over memory.

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

Proven on 2026-05-02 in draft `ER31415213` for:

- `发票抬头`: `深圳卓正光锥科技有限公司-021`
- `成本中心`: `集团职能部门 / 软件研发部 / 软件研发部`
- `是否属于研发项目费用`: `否`
- `出差类型`: `其他（请在事由处说明）`
- `出差范围`: `跨省、直辖市`

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

Proven on 2026-05-02 in draft `ER31415213`:

- range `2026-04-14 ~ 2026-04-18`
- duration `5`
- saved line `EXP1267751812`

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

- if the user already authorized continuing, click popup `确认` by ref
- otherwise stop and ask

