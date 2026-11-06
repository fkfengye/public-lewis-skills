import importlib.util
import json
import math
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'flowchart/monochrome-horizontal-collaboration@1.0.0'


def ends(path):
    parts = re.findall(r'[MHV]|-?\d+(?:\.\d+)?', path)
    x = y = None
    points = []
    i = 0
    while i < len(parts):
        command = parts[i]
        if command == 'M':
            x, y = float(parts[i + 1]), float(parts[i + 2])
            i += 3
        elif command == 'H':
            x = float(parts[i + 1])
            i += 2
        elif command == 'V':
            y = float(parts[i + 1])
            i += 2
        else:
            raise AssertionError(f'未预期的路径命令: {command}')
        points.append((x, y))
    return points[0], points[-1]


def on_rectangle(node, point):
    x, y = point
    x1, y1 = float(node.get('x')), float(node.get('y'))
    x2 = x1 + float(node.get('width'))
    y2 = y1 + float(node.get('height'))
    return (x1 - 1 <= x <= x2 + 1 and y1 - 1 <= y <= y2 + 1 and
            min(abs(x - x1), abs(x - x2), abs(y - y1), abs(y - y2)) < 1)


class MonochromeHorizontalFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_fc05', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_selection_and_old_defaults(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            result = self.catalog.resolve(ROOT, None, number='FC-05', line_style=line)
            self.assertEqual((result['key'], result['line_style']), (KEY, line))
        self.assertEqual(self.catalog.resolve(ROOT, '流程图', '黑白横向协作流程')['number'], 'FC-05')
        self.assertEqual(self.catalog.resolve(ROOT, 'flowchart')['number'], 'FC-01')
        self.assertEqual(self.catalog.resolve(ROOT, 'data-flow')['number'], 'DF-01')

    def test_model_endpoints_line_styles_and_visible_features(self):
        selected = self.catalog.resolve(ROOT, None, number='FC-05')
        svg = ET.parse(selected['example_path']).getroot()
        metadata = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual((metadata['profile'], metadata['sample_kind']), (KEY, 'synthetic'))
        own = 'styles/flowchart/monochrome-horizontal-collaboration/1.0.0/example.svg'
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in selected['dependency_hashes'].items() if k not in mutable | {own}}
        self.assertEqual({k: metadata['dependencies'][k] for k in frozen}, frozen)
        nodes = {e.get('data-node'): e for e in svg.iter() if e.get('data-node')}
        self.assertEqual(set(nodes), {n['id'] for n in metadata['model']['nodes']})
        self.assertEqual(len(nodes), 7)
        self.assertTrue(all(n.tag.endswith('rect') and n.get('fill') == '#FFFFFF' and
                            float(n.get('rx')) > 0 for n in nodes.values()))
        paths = {e.get('id'): e for e in svg.iter() if e.get('data-diagram-role') == 'connector'}
        edges = metadata['model']['edges']
        self.assertEqual(set(paths), {e['id'] for e in edges})
        for edge in edges:
            path = paths[edge['id']]
            self.assertEqual(path.get('marker-end'), 'url(#fc05-arrow)')
            start, end = ends(path.get('d'))
            self.assertTrue(on_rectangle(nodes[edge['source']], start), edge['id'])
            self.assertTrue(on_rectangle(nodes[edge['target']], end), edge['id'])
            self.assertEqual(path.get('stroke-dasharray') is not None, edge['line'] != 'solid')
        heavy = next(e for e in edges if e['line'] == 'dashed-heavy')
        self.assertIsNone(heavy['label'])
        self.assertGreater(float(paths[heavy['id']].get('stroke-width')),
                           float(paths['fc05-e1'].get('stroke-width')))
        self.assertFalse(any(e.get('data-edge-label') == heavy['id'] for e in svg.iter()))

    def test_no_original_image_added(self):
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        self.assertNotIn(KEY, index)
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="FC-05"', 1)[1].split('</article>', 1)[0]
        self.assertIn('fc05-title', card)
        self.assertNotIn('data-original=', card)
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject')
                             for e in ET.parse(ROOT / 'styles/flowchart/monochrome-horizontal-collaboration/1.0.0/example.svg').getroot().iter()))


if __name__ == '__main__':
    unittest.main()
