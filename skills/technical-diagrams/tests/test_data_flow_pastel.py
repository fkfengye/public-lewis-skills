import base64
import importlib.util
import json
import math
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'data-flow/pastel-handdrawn@1.0.0'


def path_endpoints(path):
    tokens = re.findall(r'[MHV]|-?\d+(?:\.\d+)?', path)
    x = y = None
    points = []
    i = 0
    while i < len(tokens):
        command = tokens[i]
        if command == 'M':
            x, y = float(tokens[i + 1]), float(tokens[i + 2])
            i += 3
        elif command == 'H':
            x = float(tokens[i + 1])
            i += 2
        elif command == 'V':
            y = float(tokens[i + 1])
            i += 2
        else:
            raise AssertionError(f'未预期的路径命令: {command}')
        points.append((x, y))
    return points[0], points[-1]


def boundary_distance(node, point):
    x, y = point
    if node.tag.endswith('circle'):
        return abs(math.hypot(x - float(node.get('cx')), y - float(node.get('cy'))) - float(node.get('r')))
    x1, y1 = float(node.get('x')), float(node.get('y'))
    x2, y2 = x1 + float(node.get('width')), y1 + float(node.get('height'))
    if not (x1 - 1 <= x <= x2 + 1 and y1 - 1 <= y <= y2 + 1):
        return float('inf')
    return min(abs(x-x1), abs(x-x2), abs(y-y1), abs(y-y2))


class DataFlowPastelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_df01', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_selection_and_old_defaults(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            resolved = self.catalog.resolve(ROOT, None, number='DF-01', line_style=line)
            self.assertEqual((resolved['key'], resolved['line_style']), (KEY, line))
        self.assertEqual(self.catalog.resolve(ROOT, '数据流图')['number'], 'DF-01')
        self.assertEqual(self.catalog.resolve(ROOT, 'DFD', '手绘粉彩数据流')['number'], 'DF-01')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        self.assertEqual(self.catalog.resolve(ROOT, 'topology')['number'], 'TP-01')

    def test_example_nodes_edges_and_unknown_direction(self):
        selected = self.catalog.resolve(ROOT, None, number='DF-01')
        svg = ET.parse(selected['example_path']).getroot()
        metadata = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual((metadata['sample_kind'], metadata['profile']), ('synthetic', KEY))
        own = 'styles/data-flow/pastel-handdrawn/1.0.0/example.svg'
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in selected['dependency_hashes'].items() if k not in mutable | {own}}
        self.assertEqual({k: metadata['dependencies'][k] for k in frozen}, frozen)
        nodes = {e.get('data-node'): e for e in svg.iter() if e.get('data-node')}
        shadows = {e.get('data-shadow') for e in svg.iter() if e.get('data-shadow')}
        self.assertEqual(set(nodes), {n['id'] for n in metadata['model']['nodes']})
        self.assertEqual(set(nodes), shadows)
        self.assertEqual(sum(e.tag.endswith('circle') for e in nodes.values()), 3)
        self.assertEqual(sum(e.tag.endswith('rect') for e in nodes.values()), 4)
        paths = {e.get('id'): e for e in svg.iter() if e.get('data-diagram-role') == 'connector'}
        edges = metadata['model']['edges']
        self.assertEqual(set(paths), {e['id'] for e in edges})
        self.assertEqual(sum(e['direction'] == 'unknown' for e in edges), 1)
        for edge in edges:
            path = paths[edge['id']]
            self.assertEqual(path.get('marker-end') is not None, edge['direction'] == 'forward')
            start, end = path_endpoints(path.get('d'))
            self.assertLess(boundary_distance(nodes[edge['source']], start), 1, edge['id'])
            self.assertLess(boundary_distance(nodes[edge['target']], end), 1, edge['id'])
        self.assertTrue(any(len([c for c in e if c.tag.endswith('tspan')]) > 1
                            for e in svg.iter() if e.get('data-edge-label')))
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in svg.iter()))

    def test_authorized_original_and_gallery(self):
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="DF-01"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')
        self.assertIn('df01-title', card)


if __name__ == '__main__':
    unittest.main()
