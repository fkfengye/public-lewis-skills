import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'flowchart/thin-line-component-flow@1.0.0'


class ComponentFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('fc09_catalog', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_new_profile_and_existing_defaults(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            result = self.catalog.resolve(ROOT, None, number='FC-09', line_style=line)
            self.assertEqual((result['key'], result['line_style']), (KEY, line))
        self.assertEqual(self.catalog.resolve(ROOT, 'flowchart')['number'], 'FC-01')
        self.assertEqual(self.catalog.resolve(ROOT, None, number='FC-08')['key'],
                         'flowchart/handdrawn-runtime-flow@1.0.0')

    def test_example_is_editable_and_has_explicit_semantics(self):
        result = self.catalog.resolve(ROOT, None, number='FC-09')
        svg = ET.parse(result['example_path']).getroot()
        metadata = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual((metadata['profile'], metadata['number'], metadata['sample_kind']),
                         (KEY, 'FC-09', 'synthetic'))
        features = {e.get('data-feature') for e in svg.iter() if e.get('data-feature')}
        self.assertTrue({'main-boundary', 'support-band', 'dark-storage', 'internal-cards',
                         'blue-list', 'segmented-list', 'stack', 'fan-out', 'parallel-channels',
                         'reference-bars'} <= features)
        edges = {e.get('id'): e for e in svg.iter() if e.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(edges), {edge['id'] for edge in metadata['model']['connections']})
        nodes = {node['id'] for node in metadata['model']['nodes']}
        for edge in metadata['model']['connections']:
            self.assertIn(edge['from'], nodes)
            self.assertIn(edge['to'], nodes)
            self.assertNotEqual(edge['from'], edge['to'])
            self.assertIsNone(edges[edge['id']].get('marker-start'))
            self.assertIsNotNone(edges[edge['id']].get('marker-end'))
            route = edge['routing']
            self.assertEqual(route['bends'], len(route['points']) - 2)
            length = sum(abs(a[0] - b[0]) + abs(a[1] - b[1])
                         for a, b in zip(route['points'], route['points'][1:]))
            self.assertEqual(route['length'], length)
            self.assertEqual(route['crossings'], 0)
            self.assertTrue(route['alternatives'])
            expected = 'M' + ' L'.join(f'{x} {y}' for x, y in route['points'])
            self.assertEqual(edges[edge['id']].get('d'), expected)
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in svg.iter()))

    def test_gallery_omits_original_in_public_release(self):
        references = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        self.assertEqual(references, {}, '公开版本不随附参考原图')
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="FC-09"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')

    def test_example_styles_do_not_change_other_gallery_cards(self):
        path = ROOT / 'styles/flowchart/thin-line-component-flow/1.0.0/example.svg'
        svg = ET.parse(path).getroot()
        self.assertEqual(svg.get('id'), 'fc09-diagram')
        styles = ''.join(e.text or '' for e in svg.iter() if e.tag.endswith('style'))
        for rule in styles.split('}'):
            if '{' in rule:
                for selector in rule.split('{', 1)[0].split(','):
                    self.assertTrue(selector.strip().startswith('#fc09-diagram'), selector)
        ids = [element.get('id') for element in svg.iter() if element.get('id')]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(value.startswith('fc09-') for value in ids))
        for element in svg.iter():
            if element.get('marker-end'):
                self.assertEqual(element.get('marker-end'), 'url(#fc09-arrow)')

    def test_reference_details_are_visible_in_the_gallery_example(self):
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="FC-09"', 1)[1].split('</article>', 1)[0]
        svg = ET.fromstring(card.split('<svg ', 1)[1].split('</svg>', 1)[0].join(('<svg ', '</svg>')))
        features = {element.get('data-feature'): element for element in svg.iter()
                    if element.get('data-feature')}
        for name in ('reference-bars-context', 'shared-trunk', 'rounded-branch',
                     'stack-two-white', 'stack-two-warm', 'multiline-label'):
            self.assertIn(name, features)
        self.assertGreaterEqual(sum(e.tag.endswith('rect') for e in features['stack-two-white'].iter()), 2)
        self.assertGreaterEqual(sum(e.tag.endswith('rect') for e in features['stack-two-warm'].iter()), 2)
        self.assertTrue(any('Q' in (e.get('d') or '') for e in features['rounded-branch'].iter()))
        self.assertGreaterEqual(sum(e.tag.endswith('tspan') for e in features['multiline-label'].iter()), 2)
        list_items = [e for e in features['blue-list'].iter()
                      if e.tag.endswith('text') and ''.join(e.itertext()).strip().startswith('•')]
        self.assertEqual(len(list_items), 5)
        self.assertTrue(any('…' in ''.join(e.itertext()) for e in list_items))


if __name__ == '__main__':
    unittest.main()
