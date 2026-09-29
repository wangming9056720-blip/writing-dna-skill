# _analysis

这里保存可复现的中间分析结果和证据映射，不放原始正文。

建议文件：

- corpus-stats.json：语料级统计与单文件基础统计
- language-stats.json：句长、标点、标题、图片等机械统计
- evidence-map.json：核心 Writing DNA 结论到证据来源的映射
- quality-check.json：覆盖率、缺失项、异常路径等验收结果

原则：

1. JSON 中引用原文时只保存相对路径和必要的短证据说明。
2. 不复制整篇原文。
3. 所有统计注明口径。
4. 无法验证的结论保留 unverified，不得补造数据。
