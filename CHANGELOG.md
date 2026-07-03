# Changelog

## v0.4.2-pfc5 (2026-07-03)

PFC 5.0 完整知识库版本，基于 itasca-mcp-bridge v0.4.2。
新增 PFC 5.0 实战参考指南（pfc5-guide）和完整接触模型参考。
修复 PFC 5.0 命令式语法在 knowledge 和 bridge 中的多个兼容性问题。

### 新增
- `knowledge/resources/pfc/references/pfc5-guide/`: 12 个参考指南文件
  - `syntax-overview.json` — PFC 5.0 vs 7.0+ 语法差异总览
  - `wall-creation.json` — 墙创建命令参考
  - `ball-generation.json` — 颗粒生成命令参考
  - `contact-model.json` — 接触模型设置参考（cmat, deformability）
  - `pfc5-contact-models.json` — 全部 12 个 PFC5 接触模型完整语法 + 8 个 PFC7+ 仅有的模型对比
  - `flatjoint.json` — Flat-Joint 模型完整参考（属性、方法、回调、能量）
  - `servo-control.json` — 伺服控制参考
  - `measurement.json` — 应力/应变测量参考
  - `history-recording.json` — History 记录参考
  - `fish-functions.json` — 关键 FISH 内置函数参考
  - `common-pitfalls.json` — 实战语法陷阱大全（含 12 条已验证条目）
  - `workflow-biaxial.json` — 双轴试验工作流参考
- `knowledge/resources/pfc/references/index.json`: 参考索引（链接 pfc5-guide 全部文件）
- `_compat.py`: 增加 `threading.Thread.ident` 兼容回退（Python 2.7 不支持的属性）

### 修复
- **`common-pitfalls.json`**: 修正 `history write` 语法说明
  - `history id N @func` 和 `history add id N fish @func` 在 PFC5 中都有效（非仅 add 形式）
  - `history write` 不接受 `id` 关键字或 `all` 参数，必须显式列 ID
- **`contact-model.json`**: 模型数量从 10 更新为 12（增加 rrlinear 和 burger）
- **`_compat.py`**: 增加 `threading.Thread.ident` 可选属性适配，修复 Python 2.7 下的 `Future` 错误
- **`README.md`**: 更新 PFC 5.0 知识库版本号为 v0.4.2-pfc5

### 知识库内容
- PFC 5.0 命令文档：138 条命令，14 个分类（ball, wall, clump, contact, cmat, measure, history, domain, cycle, solve, set, plot, fish, 通用）
- PFC 5.0 参考指南：12 篇实战指南（syntax, ball, wall, contact-model, pfc5-models, flatjoint, servo, measurement, history, fish, pitfalls, workflow）
- 完整的 contact-model 知识图谱：12 个 PFC5 模型 × 全部属性/方法/回调 + 8 个 PFC7+ 模型清单
