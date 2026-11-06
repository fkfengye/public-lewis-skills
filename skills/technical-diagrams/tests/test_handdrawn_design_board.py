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


def path_endpoints(path):
    tokens = re.findall(r'[MHVQ]|-?\d+(?:\.\d+)?', path)
    x = y = None
    points = []
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


class HanddrawnDesignBoardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_ar14', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_selection_and_existing_defaults(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            result = self.catalog.resolve(ROOT, None, number='AR-14', line_style=line)
            self.assertEqual((result['key'], result['line_style']), (KEY, line))
        self.assertEqual(self.catalog.resolve(ROOT, '架构图', '手绘设计讨论架构')['number'], 'AR-14')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        self.assertEqual(self.catalog.resolve(ROOT, 'data-flow')['number'], 'DF-01')

    def test_features_and_semantic_model(self):
        selected = self.catalog.resolve(ROOT, None, number='AR-14')
        svg = ET.parse(selected['example_path']).getroot()
        self.assertAlmostEqual(float(svg.get('width')) / float(svg.get('height')), 1682 / 1262, delta=.03)
        metadata = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual((metadata['profile'], metadata['sample_kind']), (KEY, 'synthetic'))
        self.assertEqual(metadata['line_style']['id'], 'rounded-orthogonal')
        own = 'styles/architecture/handdrawn-design-board/1.0.0/example.svg'
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in selected['dependency_hashes'].items() if k not in mutable | {own}}
        self.assertEqual({k: metadata['dependencies'][k] for k in frozen}, frozen)
        self.assertEqual({e.get('data-info') for e in svg.iter() if e.get('data-info')},
                         {'goal', 'constraints'})
        nodes = {e.get('data-node'): e for e in svg.iter() if e.get('data-node')}
        notes = {e.get('data-note') for e in svg.iter() if e.get('data-note')}
        icons = {e.get('data-icon') for e in svg.iter() if e.get('data-icon')}
        self.assertEqual(set(nodes), {n['id'] for n in metadata['model']['nodes']})
        self.assertEqual(notes, {n['id'] for n in metadata['model']['notes']})
        self.assertEqual(icons, {n['id'] for n in metadata['model']['icons']})
        self.assertEqual((len(nodes), len(notes), len(icons)), (7, 2, 6))
        self.assertTrue(notes.isdisjoint(nodes))
        self.assertTrue(icons.isdisjoint(nodes))
        self.assertTrue(all(item['target'] in nodes for item in metadata['model']['notes'] + metadata['model']['icons']))
        icon_groups = {e.get('data-icon'): e for e in svg.iter() if e.get('data-icon')}
        for icon in metadata['model']['icons']:
            icon_rect = next(e for e in icon_groups[icon['id']] if e.tag.endswith('rect'))
            parent = nodes[icon['target']]
            ix, iy = float(icon_rect.get('x')), float(icon_rect.get('y'))
            px, py = float(parent.get('x')), float(parent.get('y'))
            self.assertLess(max(ix, px), min(ix + float(icon_rect.get('width')), px + float(parent.get('width'))))
            self.assertLess(max(iy, py), min(iy + float(icon_rect.get('height')), py + float(parent.get('height'))))
        self.assertTrue(any(e.tag.endswith('circle') for e in nodes.values()))
        self.assertTrue(any(e.tag.endswith('rect') and float(e.get('rx')) > 0 for e in nodes.values()))
        self.assertTrue(any(e.tag.endswith('rect') and float(e.get('rx')) == 0 for e in nodes.values()))
        self.assertTrue(any(len([c for c in e if c.tag.endswith('tspan')]) >= 3
                            for e in svg.iter() if e.get('data-multiline-node')))
        self.assertTrue(any(len([c for c in e if c.tag.endswith('tspan')]) >= 2
                            for e in svg.iter() if e.get('data-edge-label')))
        marker = next(e for e in svg.iter() if e.tag.endswith('marker'))
        self.assertEqual(next(iter(marker)).get('fill'), 'none')
        paths = {e.get('id'): e for e in svg.iter() if e.get('data-diagram-role') == 'connector'}
        edges = metadata['model']['edges']
        self.assertEqual(set(paths), {e['id'] for e in edges})
        self.assertTrue(any('Q' in e.get('d') for e in paths.values()))
        self.assertTrue(any('Q' not in e.get('d') for e in paths.values()))
        for edge in edges:
            path = paths[edge['id']]
            self.assertEqual(path.get('marker-end'), 'url(#ar14-arrow)')
            start, end = path_endpoints(path.get('d'))
            self.assertLess(boundary_distance(nodes[edge['source']], start), 1, edge['id'])
            self.assertLess(boundary_distance(nodes[edge['target']], end), 1, edge['id'])
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in svg.iter()))

    def test_original_available_in_gallery(self):
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="FC-07"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')
        self.assertIn('Design workshop', card)


if __name__ == '__main__':
    unittest.main()
