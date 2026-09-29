---
name: writing-dna-evidence-layer
description: 在 writing-dna-skill 已完成的作者语料目录上，增量生成视频式证据层：_analysis/、语料索引.md、证据与方法.md，以及可选的作者包 README。只新增证据与索引，不修改 raw/、_meta/ 或五份核心 Writing DNA 产物。
---

# Writing DNA Evidence Layer

这是 writing-dna-skill 的附加证据层。它不替代原始蒸馏流程，也不重写任何既有核心产物。

## 适用时机

仅在目标作者目录已经完成正常蒸馏后执行，目录中应已有 raw/、_meta/、语言DNA.md、文章结构模板.md、写作视角与认知框架.md、视觉风格指南.md、Writing-DNA.md。英文产物同理。

## 不可破坏原则

1. 不得修改 raw/ 中的原始语料。
2. 不得修改 _meta/ 中已有元数据。
3. 不得修改、覆盖或重命名五份核心 Writing DNA 产物。
4. 已存在的 README.md、语料索引.md、证据与方法.md 不得静默覆盖。
5. 证据不足的结论必须标记为未验证/证据不足，不得补造例句、统计值或来源。
6. 本层所有结论必须可回指到 raw/、_meta/、机械统计或核心蒸馏产物。

## 新增结构

```text
作者目录/
├── _analysis/
│   ├── corpus-stats.json
│   ├── language-stats.json
│   ├── evidence-map.json
│   └── quality-check.json
├── 语料索引.md
├── 证据与方法.md
└── README.md                 # 仅当原目录没有 README.md 时创建
```

如果 README.md 已存在，不修改它；需要说明证据层时新建 README.evidence-layer.md。

## 执行流程

### Step 1：机械统计

扫描 raw/ 全部 .md/.txt，至少统计：语料文件数、非空白字符数、段落数、句子数、平均句长、短句（≤15 字符）占比、长句（≥50 字符）占比、常见标点、Markdown 标题数、Markdown 图片数、元数据覆盖率。

结果写入 _analysis/corpus-stats.json 与 _analysis/language-stats.json。

### Step 2：生成语料索引

语料索引.md 必须覆盖 raw/ 的全部文本文件。每条至少包含：文件名与相对路径、标题、日期、article_type、topic_tags、字符数、元数据是否存在。

索引的作用是让后续 Agent 先查目录，再精准挑原文，而不是每次盲扫整个 raw/。

### Step 3：建立证据映射

读取全部核心蒸馏产物，为重要结论建立 _analysis/evidence-map.json。每条至少包含：

- claim：被验证的风格结论
- layer：L1/L2/L3/L4/L5/L6
- source_type：raw / meta / script / distilled / mixed
- sources：相对路径数组
- evidence：简短证据说明，不大段复制原文
- confidence：high / medium / low / unverified
- notes：限制、反例或例外

不要为了凑数量制造证据。找不到可靠证据时保留 unverified。

### Step 4：撰写《证据与方法.md》

按模板写明：语料范围与覆盖度、机械统计方法与口径、人工/Agent 深读抽样方法、L1-L6 各层证据来源、结论可信度与局限、可复现步骤、未验证项与异常项。

它回答的是：这些 Writing DNA 结论为什么可信、怎么复核。

### Step 5：质量检查

生成 _analysis/quality-check.json，至少检查：raw 是否为空、索引覆盖率、_meta 覆盖率、核心五份文档是否存在、evidence-map 是否存在、是否出现来源不存在的证据路径。

## 最终目标

最终作者包形成三层：

1. 原始层：raw/ + _meta/
2. 证据层：_analysis/ + 语料索引.md + 证据与方法.md
3. 结论层：四份分层 DNA + Writing-DNA.md

证据层只负责可追溯、可复核、可导航，不能替代原始语料，也不能反过来篡改核心蒸馏结论。
