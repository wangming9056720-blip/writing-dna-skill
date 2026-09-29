# Writing DNA Evidence Layer

这是 writing-dna-skill 的纯增量扩展，用于把普通蒸馏成果补成更接近视频里那种实际生产用的作者文风知识包。

它只新增：

- _analysis/
- 语料索引.md
- 证据与方法.md
- 可选的作者包 README.md

它不会修改仓库原有的 SKILL.md、README、核心模板，也不会修改目标作者目录里的原始语料和五份 Writing DNA 文档。

## 使用方式

先按原项目完成正常蒸馏，然后让 Agent 读取本目录的 SKILL.md，对该作者目录执行 evidence-layer。

推荐顺序：机械统计 → 语料索引 → evidence-map → 证据与方法 → quality-check。
