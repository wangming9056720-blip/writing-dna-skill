from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    script = Path(__file__).resolve().parents[1] / 'scripts' / 'build_evidence_layer.py'
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / 'author'
        corpus = root / 'raw-corpus'
        meta = root / '_meta'
        corpus.mkdir(parents=True)
        meta.mkdir(parents=True)

        sample = '# Heading\n\nHello world. This is a test.\n\n第二段很短。![图](img.png)\n'
        (corpus / 'a.md').write_text(sample, encoding='utf-8')
        (meta / 'a.json').write_text(json.dumps({
            'title': 'Sample',
            'date': '2026-09-29',
            'article_type': 'test',
            'topic_tags': ['alpha', 'beta'],
        }, ensure_ascii=False), encoding='utf-8')

        for name in ['language-dna.md', 'structure-patterns.md', 'cognitive-framework.md', 'visual-style-guide.md', 'Writing-DNA.md']:
            (root / name).write_text('# test\n', encoding='utf-8')

        subprocess.run([sys.executable, str(script), str(root)], check=True, capture_output=True, text=True)

        corpus_stats = json.loads((root / '_analysis' / 'corpus-stats.json').read_text(encoding='utf-8'))
        language_stats = json.loads((root / '_analysis' / 'language-stats.json').read_text(encoding='utf-8'))
        quality = json.loads((root / '_analysis' / 'quality-check.json').read_text(encoding='utf-8'))
        index_text = (root / '语料索引.md').read_text(encoding='utf-8')

        assert corpus_stats['corpus_dir'] == 'raw-corpus'
        assert corpus_stats['files'][0]['non_whitespace_chars'] == len(re.sub(r'\s+', '', sample))
        assert corpus_stats['files'][0]['paragraph_count'] == 3
        assert corpus_stats['files'][0]['sentence_count'] >= 3
        assert language_stats['heading_count'] == 1
        assert language_stats['markdown_image_count'] == 1
        assert quality['core_output_set'] == 'en'
        assert all(quality['core_outputs'].values())
        assert quality['index_coverage'] == 1.0
        assert '\n' in index_text
        assert '\\n' not in index_text

        evidence = {
            'generated_at': 'test',
            'claims': [{
                'claim': 'x',
                'layer': 'L1',
                'source_type': 'raw',
                'sources': ['raw-corpus/a.md', 'raw-corpus/missing.md'],
                'confidence': 'medium',
            }],
        }
        (root / '_analysis' / 'evidence-map.json').write_text(json.dumps(evidence, ensure_ascii=False), encoding='utf-8')
        subprocess.run([sys.executable, str(script), str(root), '--force'], check=True, capture_output=True, text=True)
        quality2 = json.loads((root / '_analysis' / 'quality-check.json').read_text(encoding='utf-8'))
        assert quality2['missing_source_paths'] == ['raw-corpus/missing.md']

    print('evidence-layer smoke test: OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
