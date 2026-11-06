import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'architecture/dashed-layered-cards@1.0.0'


class DashedLayeredCardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_ar10', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_selection_and_existing_defaults(self):
        data = self.catalog.read_catalog(ROOT)
        self.assertIn('AR-10', data['style_numbers'])
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            selected = self.catalog.resolve(ROOT, None, number='AR-10', line_style=line)
            self.assertEqual(selected['key'], KEY)
            self.assertEqual(selected['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture', '蓝紫虚线分区架构')['number'], 'AR-10')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        self.assertEqual(self.catalog.resolve(ROOT, None, number='AR-09')['key'], 'architecture/three-column-feedback@1.0.0')

    def test_example_covers_layout_and_connectors(self):
        self.assertIn(KEY, self.catalog.read_catalog(ROOT)['style_numbers'].values())
        selected = self.catalog.resolve(ROOT, None, number='AR-10', line_style='rounded-orthogonal')
        svg = ET.parse(selected['example_path']).getroot()
        self.assertAlmostEqual(float(svg.get('width')) / float(svg.get('height')), 1888 / 730, delta=.03)
        meta = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        self.assertEqual(meta['profile'], KEY)
        self.assertEqual(meta['sample_kind'], 'synthetic')
        self.assertEqual(meta['line_style']['id'], 'rounded-orthogonal')
        own = 'styles/architecture/dashed-layered-cards/1.0.0/example.svg'
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in selected['dependency_hashes'].items() if k != own and k not in mutable}
        self.assertEqual({k: meta['dependencies'][k] for k in frozen}, frozen)
        model = meta['model']
        self.assertEqual(set(model['nodes']), set(model['node_owners']))
        self.assertTrue(all(e['source'] in model['nodes'] and e['target'] in model['nodes'] for e in model['edges']))
        labels = {''.join(el.itertext()).strip() for el in svg.iter() if el.tag.endswith('text')}
        self.assertTrue(set(model['nodes']).issubset(labels))
        self.assertTrue({e['label'] for e in model['edges']}.issubset(labels))
        groups = {el.get('data-group'): el for el in svg.iter() if el.get('data-group')}
        self.assertEqual(set(groups), {'support', 'access', 'core', 'collaboration'})
        self.assertTrue(all(el.get('stroke-dasharray') and float(el.get('rx')) > 0 for el in groups.values()))
        self.assertGreaterEqual(len([el for el in svg.iter() if el.get('data-node')]), 14)
        paths = {el.get('id'): el for el in svg.iter() if el.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(paths), {edge['id'] for edge in model['edges']})
        self.assertTrue(all(el.get('marker-end') and not el.get('marker-start') for el in paths.values()))
        self.assertTrue(any(el.get('stroke') == '#DC2626' for el in paths.values()))
        self.assertTrue(any(el.get('stroke') == '#7C3AED' and el.get('stroke-dasharray') for el in paths.values()))
        self.assertTrue(any('Q' in el.get('d', '') for el in paths.values()))

    def test_original_and_preview_are_in_the_card(self):
        self.assertIn(KEY, self.catalog.read_catalog(ROOT)['style_numbers'].values())
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="AR-10"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')
        self.assertIn('ar10-title', card)


if __name__ == '__main__':
    unittest.main()
