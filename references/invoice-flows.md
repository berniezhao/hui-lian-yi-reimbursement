# HuiLianYi Expense Line Recipes

Use this reference after the main `SKILL.md` plan is complete and you are operating a specific expense line.

## General Rules

- Work one line at a time.
- Upload exactly one invoice for one invoice-driven line.
- Do not use `手录费用` for airfare/train/hotel when invoice-driven flow is available.
- After OCR, read every pre-filled field before editing. OCR often fills cities and seat class correctly (hotel 城市, train 出发/到达城市 and 座等); correct only what is wrong. It can also fill a wrong value (observed: 出发城市 set to a province-level entry for the airfare line) — verify field text, not OCR success.
- Required support attachments are separate from invoice files.
- Read back each saved line and verify business values, invoice and support associations before checkpointing. Follow [ui-and-recovery.md](ui-and-recovery.md) for bounded operations, Ant control primitives (date/city pickers, React inputs, file-input targeting) and unknown-save recovery.
- Check current type-level attachment requirements as well as field-level `required`; see [api-contract.md](api-contract.md).
- Keep invoice, support and excluded source rows separate; support amounts never add a second expense. OCR and server acceptance do not prove category/date matching.

## Airfare (`发票生成费用` -> `机票`)

Goal: create a proper airfare expense line and attach the matching boarding pass.

Steps:

1. On report detail page, click `发票生成费用`.
2. Upload the airfare invoice PDF through the invoice upload area.
3. If an expense-type selector appears, choose `机票`.
4. Confirm OCR/required fields.
5. Upload the matching boarding pass to the required `附件` field.
6. Save.
7. Verify the line exists with expected date, amount, and traveler.

Critical rule:

- The airfare invoice PDF is not the boarding-pass attachment.
- Match boarding pass by flight number / route / date / traveler, not date alone.
- Same-day trip: the 开始结束日期 range is the same day clicked twice in the picker.

Known upload target for boarding pass:

- The required airfare attachment field appears below `飞机报销舱等`.
- It is a separate `附件` form item from the invoice upload area.
- The upload area has class like `upload-button-ui-box`.
- Hidden file input index can vary; identify by owning form item label, not index alone.

Useful DOM exploration:

```javascript
const activeForm = Array.from(document.querySelectorAll('.expense-form-box')).find(el => el.getClientRects().length > 0);
if (!activeForm) throw new Error('No visible expense form');
Array.from(activeForm.querySelectorAll('input[type=file]')).map((input, i) => {
  const item = input.closest('.ant-form-item, [formlabel], .expense-form-item');
  return { i, itemText: item && item.innerText, outer: input.outerHTML };
});
```

## Hotel (`发票生成费用` -> `住宿费`)

Goal: create a hotel line and attach hotel bill/order material.

Steps:

1. Click `发票生成费用`.
2. Upload the hotel invoice PDF.
3. If an expense-type selector appears, choose `住宿费`.
4. Confirm hotel fields, stay dates, amount, and merchant.
5. Upload required hotel bill/order/screenshot from DingTalk attachment data.
6. Save.
7. Verify the line exists with expected date/range, hotel, and amount.

If the form says:

- `请上传酒店订单截图或者账单`
- `未添加附件`

then invoice recognition succeeded but the required hotel support attachment is still missing. Identify the hotel attachment upload area near the lower part of the expense form, often above `事由说明`.

## Train

Use invoice-driven flow when train ticket/invoice material exists.

Check after upload:

- travel date (the ride date, not the invoice issue date — a ticket ridden 09-08 can be invoiced 09-09)
- route
- two seat fields: `座等` (usually OCR-filled) and `火车报销金额座等` (a separate required selector opened from the field; select the row cell, not the bare radio)
- amount
- required attachment validation

Railway e-invoices without an order screenshot were accepted for save (verified 2026-09-14: both train lines had invoice PDFs only); do not block on a missing order screenshot, but record it in the checkpoint if absent.

Do not assume `识别成功` means the expense line is ready; final save can still fail on required train fields.

## Subsidy (`手录费用` -> `差旅补贴`)

Only subsidy should be hand-entered.

Rules:

- 省内: RMB 100/day
- 跨省（含直辖市、港澳台）: RMB 150/day
- 国外: RMB 300/day
- Use actual trip dates, never today's default unless today is truly the trip date.

Basic steps:

1. Click `手录费用`.
2. Choose `差旅补贴`.
3. Fill `发生日期` — it defaults to today; set it to the trip start.
4. Fill `开始结束日期` with the actual trip range.
5. Verify the auto-recalculated day count.
6. Fill the amount through the React native-setter pattern (plain `fill` is unreliable on the controlled amount input; see the Ant control primitives in [ui-and-recovery.md](ui-and-recovery.md)).
7. Fill reason if needed.
8. Save.

Prefer `手录费用` for subsidy. On 2026-05-02, nearby `手录行程及差旅补贴` returned click success but no visible state change.

### Ant Range Picker

The subsidy `开始结束日期` field is an Ant readonly range picker. Plain `fill`, keyboard typing, or native DOM setters do not reliably update business state.

Stable pattern:

1. Trigger the picker with `mousedown` + `focus()` + `click()` on the input (a plain click on the field wrapper may not open it; verified 2026-09-14).
2. If a wrong range exists, click `close-circle` to clear it.
3. Click the calendar day for the start date once.
4. Click the calendar day for the end date once (same day twice for a same-day range).
5. Verify both visible inputs and the recalculated day count.

Example proven on 2026-05-02:

- range: `2026-04-14 ~ 2026-04-18`
- expected duration: `5`
- amount: `750.00`

If the picker collapses both start/end to the same date, clear it and repeat. Do not save a one-day range when the trip spans multiple days.

### Subsidy Popup

If save opens a popup containing `检查结果` or `超费用标准`:

- read the exact message and use existing explicit authorization for that override, if present
- if it requires an unauthorized business-rule override, pause the affected save and ask; do not treat informational confirmation as a new permission boundary

