# hui-lian-yi-reimbursement

Codex skill for drafting HuiLianYi (汇联易) travel reimbursement reports from DingTalk AI Table data.

This repository contains the skill instructions, configuration template, and focused references needed for Codex to:

- read trip and voucher data from the configured DingTalk AI Table
- create or continue HuiLianYi travel reimbursement drafts
- upload airfare, hotel, boarding pass, and support files
- add airfare, hotel, and travel subsidy expense lines
- stop before final submission so the user can review and submit manually

## Safety Rules

The skill is intentionally conservative because HuiLianYi is a fragile SPA and reimbursement submission is user-facing financial work.

- Codex must never click `提交` unless the user explicitly asks it to submit.
- Codex should add one expense line at a time and verify the saved result before continuing.
- Invoice-driven expenses should use `发票生成费用`; `手录费用` is reserved for `差旅补贴` unless the user says otherwise.
- New reimbursement report reasons append:

```text
（本报销单由Codex协助填写）
```

## Repository Layout

```text
.
├── SKILL.md
├── config.example.yaml
├── references/
│   ├── failure-modes.md
│   └── invoice-flows.md
├── build.sh
└── package.json
```

`SKILL.md` is the main runtime instruction file. Keep it concise and move detailed, situational workflow notes into `references/`.

## Local Configuration

Create a local config file from the example:

```bash
cp config.example.yaml config.local.yaml
```

Then set:

- `dingtalk_aitable.url`: the user's DingTalk AI Table URL
- `report_defaults`: HuiLianYi defaults such as invoice title, cost centers, travel type, travel scope, and payment receiver

Do not commit `config.local.yaml`; it can contain personal or company-specific data.

## Build

Build a distributable zip:

```bash
npm run build
```

The build output is written to `dist/` and excludes local config, cache files, `.git`, and build-only scripts.

## Maintenance

When changing behavior:

- update `SKILL.md`
- bump the skill version in `SKILL.md` using SemVer
- keep `config.example.yaml` free of private data
- prefer small, verifiable changes because browser selectors and date pickers are brittle

Before committing, run:

```bash
git diff --check
git status --short
```
