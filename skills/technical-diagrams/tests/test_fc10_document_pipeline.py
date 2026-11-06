import base64
import importlib.util
import json
import math
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'flowchart/pastel-document-pipeline@1.0.0'


def path_geometry(path):
    tokens = re.findall(r'[MLHVQ]|-?\d+(?:\.\d+)?', path)
    index = 0
    current = None
    start = None
    length = 0.0
    while index < len(tokens):
        command = tokens[index]
        index += 1
        count = {'M': 2, 'L': 2, 'H': 1, 'V': 1, 'Q': 4}[command]
        values = [float(value) for value in tokens[index:index + count]]
        index += count
        if command == 'M':
            current = (values[0], values[1])
            start = current
        elif command == 'Q':
            initial = current
            control, end = tuple(values[:2]), tuple(values[2:])
            for step in range(1, 101):
                t = step / 100
                point = tuple((1-t)**2*initial[n] + 2*(1-t)*t*control[n] + t*t*end[n] for n in (0, 1))
                length += math.dist(current, point)
                current = point
        else:
            end = ((values[0], current[1]) if command == 'H' else
                   (current[0], values[0]) if command == 'V' else tuple(values))
            length += math.dist(current, end)
            current = end
    return start, current, length


class DocumentPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('fc10_catalog', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_new_style_resolves_without_changing_existing_styles(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            result = self.catalog.resolve(ROOT, None, number='FC-10', line_style=line)
            self.assertEqual((result['key'], result['line_style']), (KEY, line))
        self.assertEqual(self.catalog.resolve(ROOT, 'flowchart')['number'], 'FC-01')
        self.assertEqual(self.catalog.resolve(ROOT, None, number='FC-09')['key'],
                         'flowchart/thin-line-component-flow@1.0.0')

    def test_gallery_contains_the_public_example_only(self):
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="FC-10"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')
        for feature in ('system-boundary', 'document-before', 'document-after', 'database',
                        'emphasis-card', 'user-bubble', 'actor', 'response-cloud'):
            self.assertIn(f'data-feature="{feature}"', card)

    def test_documents_are_reordered_and_retain_folded_corners(self):
        svg = ET.parse(ROOT / 'styles/flowchart/pastel-document-pipeline/1.0.0/example.svg').getroot()
        features = {e.get('data-feature'): e for e in svg.iter() if e.get('data-feature')}
        before = [e.get('data-doc-id') for e in features['document-before'].iter() if e.get('data-doc-id')]
        after = [e.get('data-doc-id') for e in features['document-after'].iter() if e.get('data-doc-id')]
        self.assertEqual(len(before), 3)
        self.assertEqual(set(before), set(after))
        self.assertNotEqual(before, after)
        metadata = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual(metadata['model']['documents']['before'], before)
        self.assertEqual(metadata['model']['documents']['after'], after)
        fills = {item['id']: item['fill'] for item in metadata['model']['documents']['items']}
        for group in (features['document-before'], features['document-after']):
            docs = [e for e in group.iter() if e.get('data-doc-id')]
            self.assertTrue(all(any(child.get('data-fold') == 'true' for child in doc.iter()) for doc in docs))
            for doc in docs:
                shape = next(child for child in doc if child.tag.endswith('path') and not child.get('data-fold'))
                self.assertEqual(shape.get('fill'), fills[doc.get('data-doc-id')])

    def test_example_shows_a_synthetic_multivalue_sequence(self):
        svg = ET.parse(ROOT / 'styles/flowchart/pastel-document-pipeline/1.0.0/example.svg').getroot()
        notes = [''.join(element.itertext()) for element in svg.iter() if element.get('data-note')]
        self.assertTrue(any('[' in note and ']' in note and ',' in note and '…' in note for note in notes))
        self.assertFalse(any('0.123' in note for note in notes))

    def test_gallery_typography_uses_left_aligned_bubble_lines(self):
        gallery_index = json.loads((ROOT / 'assets/gallery-examples/index.json').read_text(encoding='utf-8'))
        preview = ROOT / gallery_index[KEY]
        svg = ET.parse(preview).getroot()
        metadata = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        override = metadata['overrides']['typography']
        tokens = json.loads((ROOT / 'styles/flowchart/pastel-document-pipeline/1.0.0/tokens.json').read_text(encoding='utf-8'))
        self.assertGreaterEqual(override['title_size'] / tokens['font']['node'], 1.9)
        self.assertLessEqual(override['bubble_size'] / tokens['font']['node'], 0.85)
        title = next(e for e in svg.iter() if e.get('data-feature') == 'system-title')
        self.assertEqual(float(title.get('font-size')), override['title_size'])
        styles = ''.join(e.text or '' for e in svg.iter() if e.tag.endswith('style'))
        self.assertIn(f'[data-bubble-text]{{font-size:{override["bubble_size"]}px;font-style:italic}}', styles)
        for feature in ('user-bubble', 'response-cloud'):
            group = next(e for e in svg.iter() if e.get('data-feature') == feature)
            text = next(e for e in group.iter() if e.get('data-bubble-text'))
            self.assertEqual(text.get('text-anchor'), 'start')
            lines = [e for e in text if e.tag.endswith('tspan')]
            self.assertEqual(len(lines), 2)
            self.assertTrue(all(e.get('x') == text.get('x') for e in lines))
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="FC-10"', 1)[1].split('</article>', 1)[0]
        self.assertIn('data-typography-preview="true"', card)

    def test_svg_semantics_and_embedding_are_isolated(self):
        svg = ET.parse(ROOT / 'styles/flowchart/pastel-document-pipeline/1.0.0/example.svg').getroot()
        self.assertEqual(svg.get('id'), 'fc10-diagram')
        metadata = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual((metadata['profile'], metadata['number'], metadata['sample_kind']), (KEY, 'FC-10', 'synthetic'))
        ids = [e.get('id') for e in svg.iter() if e.get('id')]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(value.startswith('fc10-') for value in ids))
        styles = ''.join(e.text or '' for e in svg.iter() if e.tag.endswith('style'))
        for rule in styles.split('}'):
            if '{' in rule:
                self.assertTrue(all(s.strip().startswith('#fc10-diagram') for s in rule.split('{', 1)[0].split(',')))
        edges = {e.get('id'): e for e in svg.iter() if e.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(edges), {e['id'] for e in metadata['model']['connections']})
        nodes = {e['id'] for e in metadata['model']['nodes']}
        self.assertEqual(metadata['model']['containers'][0]['label'], '工单编排台')
        for node in metadata['model']['nodes']:
            self.assertTrue(node['label'])
            self.assertTrue(node['kind'])
            self.assertIn('container', node)
        input_node = next(node for node in metadata['model']['nodes'] if node['id'] == 'input')
        self.assertEqual(input_node['lines'], ['请处理这批', '巡检工单'])
        for edge in metadata['model']['connections']:
            self.assertIn(edge['from'], nodes)
            self.assertIn(edge['to'], nodes)
            self.assertNotEqual(edge['from'], edge['to'])
            self.assertIsNone(edges[edge['id']].get('marker-start'))
            self.assertEqual(edges[edge['id']].get('marker-end'), 'url(#fc10-arrow)')
            route = edge['routing']
            start, end, actual_length = path_geometry(edges[edge['id']].get('d'))
            self.assertEqual((start, end), (tuple(route['points'][0]), tuple(route['points'][-1])))
            self.assertAlmostEqual(route['length'], actual_length, delta=0.1)
            self.assertTrue(route['alternatives'])
            if route['bends']:
                candidates = [candidate for candidate in route['alternatives'] if candidate.get('feasible')]
                self.assertTrue(candidates)
                for candidate in candidates:
                    cand_start, cand_end, cand_length = path_geometry(candidate['path'])
                    self.assertEqual((cand_start, cand_end), (start, end))
                    self.assertAlmostEqual(candidate['length'], cand_length, delta=0.1)
                    self.assertEqual(candidate['crossings'], 0)
        rule_edge = next(e for e in metadata['model']['connections'] if e['id'] == 'fc10-database-intake')
        self.assertIn('规则数据', rule_edge['label'])
        self.assertEqual(rule_edge['note'], next(e.text for e in svg.iter() if e.get('data-note')))
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in svg.iter()))


if __name__ == '__main__':
    unittest.main()
