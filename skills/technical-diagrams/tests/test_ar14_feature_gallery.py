import base64
import importlib.util
import json
import math
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'architecture/handdrawn-design-board@1.0.0'
ATLAS = 'styles/architecture/handdrawn-design-board/1.0.0/feature-atlas.svg'


def path_endpoints(path):
    tokens = re.findall(r'[MHVQ]|-?\d+(?:\.\d+)?', path)
    x = y = None
    result = []
    i = 0
    while i < len(tokens):
        cmd = tokens[i]
        if cmd == 'M':
            x, y = float(tokens[i + 1]), float(tokens[i + 2])
            i += 3
        elif cmd == 'H':
            x = float(tokens[i + 1])
            i += 2
        elif cmd == 'V':
            y = float(tokens[i + 1])
            i += 2
        elif cmd == 'Q':
            x, y = float(tokens[i + 3]), float(tokens[i + 4])
            i += 5
        else:
            raise AssertionError(f'未预期的路径命令: {cmd}')
        result.append((x, y))
    return result[0], result[-1]


def boundary_distance(node, point):
    x, y = point
    if node.get('data-node') == 'learner':
        return abs(math.hypot(x - 285, y - 915) - 130)
    x1, y1 = float(node.get('x')), float(node.get('y'))
    x2, y2 = x1 + float(node.get('width')), y1 + float(node.get('height'))
    if not (x1 - 1 <= x <= x2 + 1 and y1 - 1 <= y <= y2 + 1):
        return float('inf')
    return min(abs(x-x1), abs(x-x2), abs(y-y1), abs(y-y2))


class AR14FeatureGalleryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_ar14_atlas', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)
        cls.svg = ET.parse(ROOT / ATLAS).getroot()
        cls.meta = json.loads(next(e for e in cls.svg.iter() if e.tag.endswith('metadata')).text)

    def test_explicit_gallery_and_frozen_profile(self):
        index = json.loads((ROOT / 'assets/gallery-examples/index.json').read_text(encoding='utf-8'))
        self.assertEqual(index[KEY], ATLAS)
        resolved = self.catalog.resolve(ROOT, None, number='AR-14')
        self.assertNotEqual(Path(resolved['example_path']), ROOT / ATLAS)
        self.assertEqual(self.meta['profile'], KEY)
        self.assertEqual(self.meta['sample_kind'], 'synthetic-feature-atlas')
        self.assertEqual(self.meta['line_style']['id'], 'rounded-orthogonal')
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in resolved['dependency_hashes'].items() if k not in mutable}
        self.assertEqual({k: self.meta['dependencies'][k] for k in frozen}, frozen)
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            self.assertEqual(self.catalog.resolve(ROOT, None, number='AR-14', line_style=line)['line_style'], line)

    def test_visual_features_and_distinct_annotations(self):
        svg, model = self.svg, self.meta['model']
        self.assertEqual(len([e for e in svg.iter() if e.get('stroke-dasharray')]), 2)
        nodes = {e.get('data-node'): e for e in svg.iter() if e.get('data-node')}
        notes = {e.get('data-note') for e in svg.iter() if e.get('data-note')}
        icons = {e.get('data-icon') for e in svg.iter() if e.get('data-icon')}
        self.assertEqual(set(nodes), {n['id'] for n in model['nodes']})
        self.assertEqual(notes, {n['id'] for n in model['notes']})
        self.assertEqual(icons, {n['id'] for n in model['icons']})
        self.assertEqual((len(nodes), len(notes), len(icons)), (6, 2, 6))
        self.assertTrue(notes.isdisjoint(nodes))
        self.assertTrue(icons.isdisjoint(nodes))
        self.assertTrue(all(item['target'] in nodes for item in model['notes'] + model['icons']))
        self.assertTrue(any(e.tag.endswith('pattern') for e in svg.iter()))
        paths = {e.get('id'): e for e in svg.iter() if e.get('data-diagram-role') == 'connector'}
        annotations = {e.get('id'): e for e in svg.iter() if e.get('data-diagram-role') == 'annotation'}
        self.assertEqual(set(paths), {e['id'] for e in model['edges']})
        self.assertEqual(set(annotations), {e['id'] for e in model['annotation_arrows']})
        self.assertEqual(len(paths), 9)
        self.assertEqual(len(annotations), 1)
        self.assertTrue(any(path.get('d').count('M') > 1 for path in paths.values()))
        self.assertTrue(any('Q' in path.get('d') for path in paths.values()))
        self.assertTrue(any(e.tag.endswith('marker') and next(iter(e)).get('fill') == 'none' for e in svg.iter()))
        for edge in model['edges']:
            path = paths[edge['id']]
            self.assertEqual(path.get('marker-end'), 'url(#ar14-atlas-open)')
            start, end = path_endpoints(path.get('d'))
            self.assertLess(boundary_distance(nodes[edge['source']], start), 1, edge['id'])
            self.assertLess(boundary_distance(nodes[edge['target']], end), 1, edge['id'])
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in svg.iter()))

    def test_gallery_contains_atlas_and_original(self):
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="FC-07"', 1)[1].split('</article>', 1)[0]
        self.assertIn('Design workshop', card)
        self.assertIn('question-api-to-course', card)
        self.assertIn('查看原始样例图', card)
        refs = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        self.assertEqual(base64.b64decode(card.split('data:image/png;base64,', 1)[1].split('"', 1)[0]),
                         (ROOT / refs[KEY]).read_bytes())


if __name__ == '__main__':
    unittest.main()
