---
name: writing-dna-evidence-layer
description: 在 writing-dna-skill 已完成的作者语料目录上，增量生成视频式证据层：_analysis/、语料索引.md、证据与方法.md，以及可选的作者包 README。只新增证据与索引，不修改 raw/、raw-corpus/、_meta/ 或五份核心 Writing DNA 产物。
---

# Writing DNA Evidence Layer

这是 `writing-dna-skill` 的附加证据层。它不替代原始蒸馏流程，也不重写任何既有核心产物。

## 适用时机

仅在目标作者目录已经完成正常蒸馏后执行。语料目录可以是 `raw/` 或 `raw-corpus/`；核心产物可以使用主项目规定的中文或英文文件名。

## 不可破坏原则

1. 不得修改 `raw/` 或 `raw-corpus/` 中的原始语料。
2. 不得修改 `_meta/` 中已有元数据。
3. 不得修改、覆盖或重命名五份核心 Writing DNA 产物。
4. 已存在的人工维护 `README.md`、`证据与方法.md`、`evidence-map.json` 不得静默覆盖。
5. `--force` 只允许刷新机器生成的统计、索引和质量检查，不覆盖人工证据。
6. 证据不足的结论必须标记为 `unverified`，不得补造例句、统计值或来源。

## 新增结构

```text
作者目录/
├── _analysis/
│   ├── corpus-stats.json
│   ├── language-stats.json
│   ├── evidence-map.json
│   ├── quality-check.json
│   └── README.md
├── 语料索引.md
├── 证据与方法.md
└── README.md / README.evidence-layer.md
```

## 执行

```bash
python skills/writing-dna-evidence-layer/scripts/build_evidence_layer.py <作者目录>
```

需要刷新机器统计时：

```bash
python skills/writing-dna-evidence-layer/scripts/build_evidence_layer.py <作者目录> --force
```

## 机械统计

脚本实际统计并落盘：语料文件数、非空白字符数、段落数、句子数、平均句长、短句（≤15 字符）占比、长句（≥50 字符）占比、常见标点、Markdown 标题数、Markdown 图片数、元数据覆盖率。

句子切分同时识别中文句末标点和英文句号。正则、JSON 和 Markdown 输出必须经过回归测试，禁止把转义后的 `\\n` 或 `\\s` 当成真实换行/空白规则。

## 语料索引

`语料索引.md` 必须覆盖当前使用的 `raw/` 或 `raw-corpus/` 全部 `.md/.txt` 文件，每条至少包含路径、标题、日期、`article_type`、`topic_tags`、字符数和元数据状态。

## 证据映射

`_analysis/evidence-map.json` 由 Agent 在机械统计之后补充。每条证据至少包含：`claim`、`layer`、`source_type`、`sources`、`evidence`、`confidence`、`notes`。

质量检查会真正验证 `sources` 中的相对路径是否存在；不存在的路径必须进入 `missing_source_paths`，不能固定返回空数组。

## 中英文兼容

质量检查按实际存在情况识别下列核心输出：

- 中文：`语言DNA.md`、`文章结构模板.md`、`写作视角与认知框架.md`、`视觉风格指南.md`、`Writing-DNA.md`
- 英文：`language-dna.md`、`structure-patterns.md`、`cognitive-framework.md`、`visual-style-guide.md`、`Writing-DNA.md`

## 最终目标

作者包形成三层：原始层（语料 + 元数据）、证据层（统计 + 索引 + 方法 + evidence-map）、结论层（四份分层 DNA + `Writing-DNA.md`）。证据层只能用于可追溯、可复核和导航，不能反过来篡改原始语料或核心蒸馏结论。
