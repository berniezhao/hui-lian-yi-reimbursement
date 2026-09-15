# hui-lian-yi-reimbursement

AI 智能体技能：从钉钉 AI 表格数据起草汇联易差旅报销单。

本仓库包含智能体所需的技能说明、配置模板和重点参考资料，用于：

- 从配置好的钉钉 AI 表格读取差旅和凭证数据
- 创建或继续汇联易差旅报销草稿
- 上传机票、酒店、登机牌和辅助材料
- 添加机票、酒店及差旅补贴费用行
- 在最终提交前停止，让用户自行复核并手动提交

## 安全规则

此技能故意保持保守，因为汇联易是一个脆弱的单页应用，报销提交流程属于面向用户的财务操作。

- 除非用户明确要求提交，否则智能体绝不能点击 `提交`。
- 智能体应该一次只添加一条费用行，并在继续前验证保存结果。
- 发票驱动的费用应使用 `发票生成费用`；`手录费用` 仅用于 `差旅补贴`，除非用户另有说明。
- 新报销单的事由需追加签名行：

```text
（本报销单由<实际执行的智能体>协助填写）
```

签名名称的解析顺序：配置里的 `report_defaults.agent_signature` → `scripts/detect-agent.py` 按环境变量探测宿主 → 回落为 `AI助手`。不要让模型凭自我认知填写，因为同一会话中可能同时存在多个智能体的环境变量。

## 仓库结构

```text
.
├── SKILL.md
├── config.example.yaml
├── references/
│   ├── failure-modes.md
│   └── invoice-flows.md
├── scripts/
│   ├── browser-auth-probe.py
│   └── detect-agent.py
├── build.sh
└── package.json
```

`SKILL.md` 是主要的运行时指令文件。请保持其简洁，并将详细的情景化流程说明放入 `references/`。

## 本地配置

从示例创建本地配置文件：

```bash
cp config.example.yaml config.local.yaml
```

然后设置：

- `dingtalk_aitable.url`：用户的钉钉 AI 表格 URL
- `report_defaults`：汇联易默认值，例如发票抬头、成本中心、出差类型、出差范围和收款方

不要提交 `config.local.yaml`；该文件可能包含个人或公司特定的数据。

## 构建

构建可发布的 zip 包：

```bash
npm run build
```

构建输出写入 `dist/`，并排除本地配置、缓存文件、`.git` 和仅用于构建的脚本。

## 维护

修改行为时：

- 更新 `SKILL.md`
- 在 `SKILL.md` 中使用语义化版本号提升技能版本
- 保持 `config.example.yaml` 无私有数据
- 优先采用小而可验证的改动，因为浏览器选择器和日期选择器易碎

提交前运行：

```bash
git diff --check
git status --short
```
