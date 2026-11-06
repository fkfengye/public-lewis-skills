import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'architecture/stacked-layer-matrix@1.0.0'


class StackedLayerMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_ar11', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_selection_and_existing_defaults(self):
        self.assertIn('AR-11', self.catalog.read_catalog(ROOT)['style_numbers'])
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            selected = self.catalog.resolve(ROOT, None, number='AR-11', line_style=line)
            self.assertEqual(selected['key'], KEY)
            self.assertEqual(selected['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture', '浅色横向分层矩阵')['number'], 'AR-11')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        self.assertEqual(self.catalog.resolve(ROOT, None, number='AR-10')['key'], 'architecture/dashed-layered-cards@1.0.0')

    def test_example_covers_layer_structure_and_model(self):
        self.assertIn(KEY, self.catalog.read_catalog(ROOT)['style_numbers'].values())
        selected = self.catalog.resolve(ROOT, None, number='AR-11')
        svg = ET.parse(selected['example_path']).getroot()
        self.assertAlmostEqual(float(svg.get('width')) / float(svg.get('height')), 1280 / 776, delta=.03)
        meta = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        self.assertEqual(meta['profile'], KEY)
        self.assertEqual(meta['sample_kind'], 'synthetic')
        own = 'styles/architecture/stacked-layer-matrix/1.0.0/example.svg'
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in selected['dependency_hashes'].items() if k != own and k not in mutable}
        self.assertEqual({k: meta['dependencies'][k] for k in frozen}, frozen)
        layers = [el for el in svg.iter() if el.get('data-layer')]
        self.assertEqual(len(layers), 4)
        self.assertTrue(all(el.get('rx') in (None, '0') for el in layers))
        for role, count in (('entry-card', 4), ('orchestrator', 3), ('matrix-card', 4), ('guard-card', 5)):
            self.assertEqual(len([el for el in svg.iter() if el.get('data-card') == role]), count)
        self.assertGreaterEqual(len([el for el in svg.iter() if el.get('data-cell')]), 25)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-summary')]), 3)
        arrows = [el for el in svg.iter() if el.get('data-diagram-role') == 'connector']
        self.assertEqual(len(arrows), 3)
        self.assertTrue(all(el.get('d', '').rstrip().endswith('Z') for el in arrows))
        self.assertEqual(len(meta['model']['edges']), 3)
        self.assertTrue(all(e['source'] in meta['model']['layers'] and e['target'] in meta['model']['layers'] for e in meta['model']['edges']))
        self.assertTrue(any(el.tag.endswith('tspan') for el in svg.iter()))

    def test_authorized_original_and_preview(self):
        self.assertIn(KEY, self.catalog.read_catalog(ROOT)['style_numbers'].values())
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="AR-11"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')
        self.assertIn('ar11-title', card)


if __name__ == '__main__':
    unittest.main()
