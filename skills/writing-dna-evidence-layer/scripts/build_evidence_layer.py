#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TEXT_EXTS = {'.md', '.txt'}
CORE_ZH = ['语言DNA.md','文章结构模板.md','写作视角与认知框架.md','视觉风格指南.md','Writing-DNA.md']
PUNCT = '，。！？；：、—（）“”‘’!?;:,'
SENT_RE = re.compile(r'[^。！？!?…]+[。！？!?…]*')
IMG_RE = re.compile(r'!\\[[^\\]]*\\]\\([^\\)]+\\)')
HEAD_RE = re.compile(r'(?m)^#{1,6}\\s+')
WS_RE = re.compile(r'\\s+')

def iso_now():
    return datetime.now(timezone.utc).isoformat()

def read_text(p):
    return p.read_text(encoding='utf-8', errors='replace')

def nows(text):
    return len(WS_RE.sub('', text))

def paras(text):
    return [x.strip() for x in re.split(r'\\n\\s*\\n+', text) if x.strip()]

def sents(text):
    out=[]
    for m in SENT_RE.findall(text):
        s=WS_RE.sub('',m)
        if s:
            out.append(s)
    return out

def find_meta(meta_dir, raw_file):
    if not meta_dir.exists():
        return None, {}
    for p in [meta_dir/(raw_file.stem+'.json'), meta_dir/(raw_file.name+'.json')]:
        if p.exists():
            try:
                d=json.loads(read_text(p))
                return p, d if isinstance(d,dict) else {}
            except Exception:
                return p, {}
    return None, {}

def stats_for(path, root, meta_dir):
    text=read_text(path)
    ss=sents(text)
    lens=[nows(x) for x in ss]
    mp, meta=find_meta(meta_dir,path)
    punct=Counter(ch for ch in text if ch in PUNCT)
    return {
      'path':path.relative_to(root).as_posix(),
      'title':meta.get('title') or path.stem,
      'date':meta.get('date'),
      'article_type':meta.get('article_type'),
      'topic_tags':meta.get('topic_tags') or [],
      'non_whitespace_chars':nows(text),
      'paragraph_count':len(paras(text)),
      'sentence_count':len(ss),
      'avg_sentence_chars':round(sum(lens)/len(lens),2) if lens else 0,
      'short_sentence_ratio':round(sum(1 for n in lens if n<=15)/len(lens),4) if lens else 0,
      'long_sentence_ratio':round(sum(1 for n in lens if n>=50)/len(lens),4) if lens else 0,
      'heading_count':len(HEAD_RE.findall(text)),
      'markdown_image_count':len(IMG_RE.findall(text)),
      'punctuation':dict(sorted(punct.items())),
      'meta_path':mp.relative_to(root).as_posix() if mp else None,
      'meta_present':mp is not None
    }

def write_text(path, text, force=False):
    if path.exists() and not force:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return True

def write_json(path, data, force=False):
    return write_text(path, json.dumps(data,ensure_ascii=False,indent=2)+'\\n', force)

def build_index(items):
    meta=sum(1 for x in items if x['meta_present'])
    total=sum(x['non_whitespace_chars'] for x in items)
    lines=['# 语料索引','', '> 本文件由 evidence-layer 机械生成，是 raw/ 的导航层，不替代原始语料。','',
           '## 语料概览','',
           f'- 语料文件数：{len(items)}',
           f'- 元数据覆盖数：{meta}',
           f'- 元数据覆盖率：{(meta/len(items)):.1%}' if items else '- 元数据覆盖率：0.0%',
           f'- 总非空白字符数：{total}','',
           '## 全量索引','',
           '| # | 标题 | 日期 | 类型 | 主题标签 | 字符数 | 元数据 | 原文路径 |',
           '|---:|---|---|---|---|---:|---|---|']
    for i,x in enumerate(items,1):
        tags='、'.join(str(t) for t in x.get('topic_tags') or [])
        lines.append(f"| {i} | {x.get('title','')} | {x.get('date') or ''} | {x.get('article_type') or ''} | {tags} | {x['non_whitespace_chars']} | {'有' if x['meta_present'] else '缺失'} | {x['path']} |")
    lines += ['', '## 使用说明','', '后续写作挑选相关原文时，优先按 article_type、topic_tags、日期筛选，再进入 raw/ 通读原文。','']
    return '\\n'.join(lines)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('author_dir',type=Path)
    ap.add_argument('--force',action='store_true')
    a=ap.parse_args()
    root=a.author_dir.resolve()
    raw=root/'raw'
    meta=root/'_meta'
    ana=root/'_analysis'
    if not raw.is_dir():
        raise SystemExit('raw directory not found: '+str(raw))
    files=sorted(p for p in raw.rglob('*') if p.is_file() and p.suffix.lower() in TEXT_EXTS)
    items=[stats_for(p,root,meta) for p in files]
    punct=Counter()
    for x in items:
        punct.update(x['punctuation'])
    corpus={
      'generated_at':iso_now(),
      'author_dir':root.name,
      'raw_file_count':len(items),
      'meta_file_count_matched':sum(1 for x in items if x['meta_present']),
      'non_whitespace_chars':sum(x['non_whitespace_chars'] for x in items),
      'paragraph_count':sum(x['paragraph_count'] for x in items),
      'sentence_count':sum(x['sentence_count'] for x in items),
      'files':items
    }
    language={
      'generated_at':iso_now(),
      'method':{'short_sentence':'<=15 chars','long_sentence':'>=50 chars','image_count':'Markdown image syntax only'},
      'punctuation':dict(sorted(punct.items())),
      'heading_count':sum(x['heading_count'] for x in items),
      'markdown_image_count':sum(x['markdown_image_count'] for x in items)
    }
    coverage=(sum(1 for x in items if x['meta_present'])/len(items)) if items else 0
    core={n:(root/n).exists() for n in CORE_ZH}
    quality={
      'generated_at':iso_now(),
      'raw_file_count':len(items),
      'index_coverage':1.0 if items else 0.0,
      'meta_coverage':round(coverage,4),
      'core_outputs':core,
      'missing_source_paths':[],
      'warnings':[m for m in [
        'raw/ is empty' if not items else None,
        'metadata coverage below 80%' if items and coverage<0.8 else None,
        'one or more core outputs are missing' if not all(core.values()) else None
      ] if m]
    }
    ana.mkdir(parents=True,exist_ok=True)
    writes={}
    writes['_analysis/corpus-stats.json']=write_json(ana/'corpus-stats.json',corpus,a.force)
    writes['_analysis/language-stats.json']=write_json(ana/'language-stats.json',language,a.force)
    writes['_analysis/quality-check.json']=write_json(ana/'quality-check.json',quality,a.force)
    writes['语料索引.md']=write_text(root/'语料索引.md',build_index(items),a.force)
    print(json.dumps({'author_dir':str(root),'writes':writes},ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
