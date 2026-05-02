# HuiLianYi Expense Line Recipes

Use this reference after the main `SKILL.md` plan is complete and you are operating a specific expense line.

## General Rules

- Work one line at a time.
- Upload exactly one invoice for one invoice-driven line.
- Do not use `手录费用` for airfare/train/hotel when invoice-driven flow is available.
- Required support attachments are separate from invoice files.
- Verify visible line creation after save.

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

Known upload target for boarding pass:

- The required airfare attachment field appears below `飞机报销舱等`.
- It is a separate `附件` form item from the invoice upload area.
- The upload area has class like `upload-button-ui-box`.
- Hidden file input index can vary; identify by owning form item label, not index alone.

Useful DOM exploration:

```javascript
Array.from(document.querySelectorAll('input[type=file]')).map((input, i) => {
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

- travel date
- route
- seat class
- amount
- required attachment validation

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
3. Fill amount.
4. Fill `发生日期`.
5. Fill `开始结束日期`.
6. Verify day count.
7. Fill reason if needed.
8. Save.

Prefer `手录费用` for subsidy. On 2026-05-02, nearby `手录行程及差旅补贴` returned click success but no visible state change.

### Ant Range Picker

The subsidy `开始结束日期` field is an Ant readonly range picker. Plain `fill`, keyboard typing, or native DOM setters do not reliably update business state.

Stable pattern:

1. Click the range field.
2. If a wrong range exists, click `close-circle` to clear it.
3. Click the calendar day for the start date once.
4. Click the calendar day for the end date once.
5. Verify both visible inputs and the recalculated day count.

Example proven on 2026-05-02:

- range: `2026-04-14 ~ 2026-04-18`
- expected duration: `5`
- amount: `750.00`

If the picker collapses both start/end to the same date, clear it and repeat. Do not save a one-day range when the trip spans multiple days.

### Subsidy Popup

If save opens a popup containing `检查结果` or `超费用标准`:

- click `确认` only if the user has explicitly authorized continuing
- otherwise pause and ask

