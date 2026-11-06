import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = 'styles/sequence/pale-folded-notes/1.0.0/example.svg'
KEY = 'sequence/pale-folded-notes@1.0.0'


class FoldedNotesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('sq04_catalog', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)
        cls.svg = ET.parse(ROOT / EXAMPLE).getroot()
        cls.meta = json.loads(next(e for e in cls.svg.iter() if e.tag.endswith('metadata')).text)

    def test_resolution_and_frozen_dependencies(self):
        resolved = self.catalog.resolve(ROOT, None, number='SQ-04')
        self.assertEqual(resolved['key'], KEY)
        self.assertTrue(resolved['frozen'])
        hashes = dict(resolved['dependency_hashes'])
        hashes.pop(EXAMPLE)
        # 入口文档随新增功能更新；固定示例保留创建时的入口摘要。
        evolving = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        self.assertEqual({k: v for k, v in hashes.items() if k not in evolving},
                         {k: v for k, v in self.meta['dependencies'].items() if k not in evolving})
        self.assertEqual(self.catalog.resolve(ROOT, 'sequence')['number'], 'SQ-01')
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            self.assertEqual(self.catalog.resolve(ROOT, None, number='SQ-04', line_style=line)['line_style'], line)

    def test_visible_elements_and_semantics(self):
        participants = {e.get('data-participant') for e in self.svg.iter() if e.get('data-participant')}
        lifelines = {e.get('data-lifeline') for e in self.svg.iter() if e.get('data-lifeline')}
        self.assertEqual(participants, lifelines)
        self.assertEqual(participants, {p['id'] for p in self.meta['model']['participants']})
        paths = {e.get('id'): e for e in self.svg.iter() if e.get('data-diagram-role') == 'connector'}
        messages = self.meta['model']['messages']
        self.assertEqual(set(paths), {m['id'] for m in messages})
        positions = {'reader': 120, 'portal': 500, 'store': 885, 'dispatch': 1300}
        for message in messages:
            path = paths[message['id']]
            self.assertTrue(path.get('marker-end'))
            if message['kind'] == 'self':
                self.assertIn('Q', path.get('d'))
                self.assertTrue(path.get('d').endswith('H' + str(positions[message['source']])))
            else:
                self.assertTrue(path.get('d').startswith('M' + str(positions[message['source']]) + ' '))
                self.assertTrue(path.get('d').endswith('H' + str(positions[message['target']])))
                self.assertEqual(bool(path.get('stroke-dasharray')), message['kind'] == 'response')
        notes = [e for e in self.svg.iter() if e.get('data-note')]
        self.assertEqual({e.get('data-note') for e in notes}, {n['id'] for n in self.meta['model']['notes']})
        self.assertTrue(all('L' in list(e)[0].get('d') for e in notes))
        self.assertIn('M460 1110 H1320', list(notes[1])[0].get('d'))
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in self.svg.iter()))

    def test_gallery_without_original(self):
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="SQ-04"', 1)[1].split('</article>', 1)[0]
        self.assertIn('图书借阅协作', card)
        self.assertNotIn('查看原始样例图', card)
        refs = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        self.assertEqual(refs, {}, '公开版本不随附参考原图')


if __name__ == '__main__':
    unittest.main()
