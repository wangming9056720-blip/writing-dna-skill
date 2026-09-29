#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TEXT_EXTS = {'.md', '.txt'}
CORPUS_DIR_NAMES = ('raw', 'raw-corpus')
CORE_ZH = ['语言DNA.md', '文章结构模板.md', '写作视角与认知框架.md', '视觉风格指南.md', 'Writing-DNA.md']
CORE_EN = ['language-dna.md', 'structure-patterns.md', 'cognitive-framework.md', 'visual-style-guide.md', 'Writing-DNA.md']
PUNCT = '，。！？；：、—（）“”‘’!?;:,.'
SENT_RE = re.compile(r'[^。！？!?….]+(?:[。！？!?….]+|$)')
IMG_RE = re.compile(r'!\[[^\]]*\]\([^)]+\)')
HEAD_RE = re.compile(r'(?m)^#{1,6}\s+')
WS_RE = re.compile(r'\s+')
PARA_RE = re.compile(r'\n\s*\n+')


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def write_text(path: Path, text: str, force: bool = False) -> bool:
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    return True


def write_json(path: Path, data: Any, force: bool = False) -> bool:
    return write_text(path, json.dumps(data, ensure_ascii=False, indent=2) + '\n', force)


def non_ws_len(text: str) -> int:
    return len(WS_RE.sub('', text))


def paragraphs(text: str) -> list[str]:
    return [p.strip() for p in PARA_RE.split(text) if p.strip()]


def sentences(text: str) -> list[str]:
    out = []
    for match in SENT_RE.findall(text):
        s = WS_RE.sub('', match)
        if s:
            out.append(s)
    return out


def choose_corpus_dir(root: Path) -> tuple[Path, list[str]]:
    existing = [root / name for name in CORPUS_DIR_NAMES if (root / name).is_dir()]
    if not existing:
        raise SystemExit('No corpus directory found. Expected raw/ or raw-corpus/.')
    warnings = []
    if len(existing) > 1:
        warnings.append('Both raw/ and raw-corpus/ exist; using the first non-empty corpus directory.')
    for directory in existing:
        if any(p.is_file() and p.suffix.lower() in TEXT_EXTS for p in directory.rglob('*')):
            return directory, warnings
    return existing[0], warnings


def parse_simple_markdown_meta(text: str) -> dict[str, Any]:
    body = text
    if text.startswith('---'):
        parts = text.split('---', 2)
        if len(parts) >= 3:
            body = parts[1]
    data: dict[str, Any] = {}
    for line in body.splitlines():
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        key = key.strip()
        value = value.strip()
        if not key or not value:
            continue
        if value.startswith('[') and value.endswith(']'):
            inner = value[1:-1].strip()
            data[key] = [x.strip().strip('"\'') for x in inner.split(',') if x.strip()]
        else:
            data[key] = value.strip('"\'')
    return data


def load_meta(path: Path) -> dict[str, Any]:
    try:
        if path.suffix.lower() == '.json':
            data = json.loads(read_text(path))
            return data if isinstance(data, dict) else {}
        if path.suffix.lower() == '.md':
            return parse_simple_markdown_meta(read_text(path))
    except Exception:
        return {}
    return {}


def find_meta(meta_dir: Path, corpus_dir: Path, raw_file: Path) -> tuple[Path | None, dict[str, Any]]:
    if not meta_dir.exists():
        return None, {}
    relative = raw_file.relative_to(corpus_dir)
    candidates = [
        meta_dir / relative.with_suffix('.json'),
        meta_dir / relative.with_suffix('.md'),
        meta_dir / f'{raw_file.stem}.json',
        meta_dir / f'{raw_file.stem}.md',
        meta_dir / f'{raw_file.name}.json',
        meta_dir / f'{raw_file.name}.md',
    ]
    seen = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            return candidate, load_meta(candidate)
    return None, {}


def file_stats(path: Path, root: Path, corpus_dir: Path, meta_dir: Path) -> dict[str, Any]:
    text = read_text(path)
    ps = paragraphs(text)
    ss = sentences(text)
    lens = [non_ws_len(s) for s in ss]
    meta_path, meta = find_meta(meta_dir, corpus_dir, path)
    punctuation = Counter(ch for ch in text if ch in PUNCT)
    return {
        'path': path.relative_to(root).as_posix(),
        'title': meta.get('title') or path.stem,
        'date': meta.get('date'),
        'article_type': meta.get('article_type'),
        'topic_tags': meta.get('topic_tags') or [],
        'non_whitespace_chars': non_ws_len(text),
        'paragraph_count': len(ps),
        'sentence_count': len(ss),
        'sentence_chars_total': sum(lens),
        'short_sentence_count': sum(1 for n in lens if n <= 15),
        'long_sentence_count': sum(1 for n in lens if n >= 50),
        'avg_sentence_chars': round(sum(lens) / len(lens), 2) if lens else 0,
        'short_sentence_ratio': round(sum(1 for n in lens if n <= 15) / len(lens), 4) if lens else 0,
        'long_sentence_ratio': round(sum(1 for n in lens if n >= 50) / len(lens), 4) if lens else 0,
        'heading_count': len(HEAD_RE.findall(text)),
        'markdown_image_count': len(IMG_RE.findall(text)),
        'punctuation': dict(sorted(punctuation.items())),
        'meta_path': meta_path.relative_to(root).as_posix() if meta_path else None,
        'meta_present': meta_path is not None,
    }


def escape_cell(value: Any) -> str:
    return str(value if value is not None else '').replace('|', '\\|').replace('\n', ' ')


def build_index(items: list[dict[str, Any]], corpus_name: str) -> str:
    total_chars = sum(x['non_whitespace_chars'] for x in items)
    meta_count = sum(1 for x in items if x['meta_present'])
    coverage = meta_count / len(items) if items else 0
    dates = sorted(str(x['date']) for x in items if x.get('date'))
    types = Counter(str(x['article_type']) for x in items if x.get('article_type'))
    tags = Counter(str(tag) for x in items for tag in (x.get('topic_tags') or []) if tag is not None)

    lines = [
        '# 语料索引',
        '',
        f'> 本文件由 evidence-layer 机械生成，是 `{corpus_name}/` 的导航层，不替代原始语料。',
        '',
        '## 语料概览',
        '',
        f'- 语料文件数：{len(items)}',
        f'- 元数据覆盖数：{meta_count}',
        f'- 元数据覆盖率：{coverage:.1%}',
        f'- 总非空白字符数：{total_chars}',
        f"- 日期范围：{(dates[0] + ' ～ ' + dates[-1]) if dates else '未提供'}",
        f"- 主要 article_type：{', '.join(f'{k}({v})' for k, v in types.most_common(8)) or '未提供'}",
        f"- 主要 topic_tags：{', '.join(f'{k}({v})' for k, v in tags.most_common(12)) or '未提供'}",
        '',
        '## 全量索引',
        '',
        '| # | 标题 | 日期 | 类型 | 主题标签 | 字符数 | 元数据 | 原文路径 |',
        '|---:|---|---|---|---|---:|---|---|',
    ]
    for i, item in enumerate(items, 1):
        tags_text = '、'.join(str(t) for t in (item.get('topic_tags') or []))
        lines.append(
            f"| {i} | {escape_cell(item.get('title'))} | {escape_cell(item.get('date'))} | "
            f"{escape_cell(item.get('article_type'))} | {escape_cell(tags_text)} | "
            f"{item['non_whitespace_chars']} | {'有' if item['meta_present'] else '缺失'} | "
            f"`{escape_cell(item['path'])}` |"
        )
    lines += [
        '',
        '## 使用说明',
        '',
        '后续写作挑选相关原文时，优先按 `article_type`、`topic_tags`、日期筛选，再进入原始语料目录通读原文。',
        '',
    ]
    return '\n'.join(lines)


def choose_core_outputs(root: Path) -> tuple[str, list[str], dict[str, bool]]:
    zh_score = sum((root / name).exists() for name in CORE_ZH)
    en_score = sum((root / name).exists() for name in CORE_EN)
    if en_score > zh_score:
        names = CORE_EN
        label = 'en'
    else:
        names = CORE_ZH
        label = 'zh'
    return label, names, {name: (root / name).exists() for name in names}


def validate_evidence_sources(root: Path, evidence_path: Path) -> tuple[list[str], str | None]:
    if not evidence_path.exists():
        return [], None
    try:
        data = json.loads(read_text(evidence_path))
    except Exception as exc:
        return [], f'evidence-map.json is invalid JSON: {exc}'
    missing = []
    for claim in data.get('claims', []) if isinstance(data, dict) else []:
        if not isinstance(claim, dict):
            continue
        for source in claim.get('sources', []) or []:
            if not isinstance(source, str):
                continue
            rel = Path(source)
            if rel.is_absolute() or not (root / rel).exists():
                missing.append(source)
    return sorted(set(missing)), None


def index_coverage(index_path: Path, items: list[dict[str, Any]]) -> float:
    if not items or not index_path.exists():
        return 0.0
    text = read_text(index_path)
    matched = sum(1 for item in items if item['path'] in text)
    return round(matched / len(items), 4)


def copy_template_if_absent(template_dir: Path, template_name: str, destination: Path) -> bool:
    source = template_dir / template_name
    if destination.exists() or not source.exists():
        return False
    return write_text(destination, read_text(source), False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('author_dir', type=Path)
    parser.add_argument(
        '--force',
        action='store_true',
        help='Refresh machine-generated stats/index/quality files. Human evidence files are never overwritten.',
    )
    args = parser.parse_args()

    root = args.author_dir.resolve()
    corpus_dir, corpus_warnings = choose_corpus_dir(root)
    meta_dir = root / '_meta'
    analysis_dir = root / '_analysis'
    template_dir = Path(__file__).resolve().parents[1] / 'templates'

    raw_files = sorted(
        p for p in corpus_dir.rglob('*')
        if p.is_file() and p.suffix.lower() in TEXT_EXTS
    )
    items = [file_stats(p, root, corpus_dir, meta_dir) for p in raw_files]

    sentence_count = sum(x['sentence_count'] for x in items)
    sentence_chars_total = sum(x['sentence_chars_total'] for x in items)
    short_count = sum(x['short_sentence_count'] for x in items)
    long_count = sum(x['long_sentence_count'] for x in items)
    punctuation = Counter()
    for item in items:
        punctuation.update(item['punctuation'])

    corpus_stats = {
        'generated_at': iso_now(),
        'author_dir': root.name,
        'corpus_dir': corpus_dir.name,
        'raw_file_count': len(items),
        'meta_file_count_matched': sum(1 for x in items if x['meta_present']),
        'non_whitespace_chars': sum(x['non_whitespace_chars'] for x in items),
        'paragraph_count': sum(x['paragraph_count'] for x in items),
        'sentence_count': sentence_count,
        'files': items,
    }

    language_stats = {
        'generated_at': iso_now(),
        'method': {
            'sentence_split': 'Chinese/ASCII sentence-ending punctuation including period',
            'short_sentence': '<=15 non-whitespace characters',
            'long_sentence': '>=50 non-whitespace characters',
            'image_count': 'Markdown image syntax only',
        },
        'avg_sentence_chars': round(sentence_chars_total / sentence_count, 2) if sentence_count else 0,
        'short_sentence_ratio': round(short_count / sentence_count, 4) if sentence_count else 0,
        'long_sentence_ratio': round(long_count / sentence_count, 4) if sentence_count else 0,
        'punctuation': dict(sorted(punctuation.items())),
        'heading_count': sum(x['heading_count'] for x in items),
        'markdown_image_count': sum(x['markdown_image_count'] for x in items),
    }

    analysis_dir.mkdir(parents=True, exist_ok=True)
    index_path = root / '语料索引.md'
    evidence_path = analysis_dir / 'evidence-map.json'

    writes: dict[str, bool] = {}
    writes['_analysis/corpus-stats.json'] = write_json(analysis_dir / 'corpus-stats.json', corpus_stats, args.force)
    writes['_analysis/language-stats.json'] = write_json(analysis_dir / 'language-stats.json', language_stats, args.force)
    writes['语料索引.md'] = write_text(index_path, build_index(items, corpus_dir.name), args.force)

    if not evidence_path.exists():
        writes['_analysis/evidence-map.json'] = write_json(
            evidence_path, {'generated_at': iso_now(), 'claims': []}, False
        )
    else:
        writes['_analysis/evidence-map.json'] = False

    writes['_analysis/README.md'] = copy_template_if_absent(
        template_dir, '_analysis/README.md', analysis_dir / 'README.md'
    )
    writes['证据与方法.md'] = copy_template_if_absent(
        template_dir, '证据与方法.md', root / '证据与方法.md'
    )
    readme_dest = root / ('README.evidence-layer.md' if (root / 'README.md').exists() else 'README.md')
    writes[readme_dest.name] = copy_template_if_absent(
        template_dir, 'author-package-README.md', readme_dest
    )

    meta_coverage = (sum(1 for x in items if x['meta_present']) / len(items)) if items else 0
    core_set, _, core_outputs = choose_core_outputs(root)
    missing_sources, evidence_error = validate_evidence_sources(root, evidence_path)
    warnings = list(corpus_warnings)
    if not items:
        warnings.append(f'{corpus_dir.name}/ is empty')
    if items and meta_coverage < 0.8:
        warnings.append('metadata coverage below 80%')
    if not all(core_outputs.values()):
        warnings.append(f'one or more {core_set} core outputs are missing')
    if evidence_error:
        warnings.append(evidence_error)
    if missing_sources:
        warnings.append('evidence-map contains missing source paths')

    quality = {
        'generated_at': iso_now(),
        'corpus_dir': corpus_dir.name,
        'raw_file_count': len(items),
        'index_coverage': index_coverage(index_path, items),
        'meta_coverage': round(meta_coverage, 4),
        'core_output_set': core_set,
        'core_outputs': core_outputs,
        'evidence_map_present': evidence_path.exists(),
        'missing_source_paths': missing_sources,
        'warnings': warnings,
    }
    writes['_analysis/quality-check.json'] = write_json(
        analysis_dir / 'quality-check.json', quality, args.force
    )

    print(json.dumps({'author_dir': str(root), 'writes': writes, 'quality': quality}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
