import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'architecture/blue-layered-icon-panels@1.0.0'


class BlueLayeredIconPanelsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_ar12', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_selection_and_existing_defaults(self):
        self.assertIn('AR-12', self.catalog.read_catalog(ROOT)['style_numbers'])
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            selected = self.catalog.resolve(ROOT, None, number='AR-12', line_style=line)
            self.assertEqual(selected['key'], KEY)
            self.assertEqual(selected['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture', '浅蓝图标分层面板')['number'], 'AR-12')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        self.assertEqual(self.catalog.resolve(ROOT, 'timeline')['number'], 'TL-01')

    def test_example_covers_panels_icons_arrows_and_model(self):
        self.assertIn(KEY, self.catalog.read_catalog(ROOT)['style_numbers'].values())
        selected = self.catalog.resolve(ROOT, None, number='AR-12')
        svg = ET.parse(selected['example_path']).getroot()
        self.assertAlmostEqual(float(svg.get('width')) / float(svg.get('height')), 2182 / 1697, delta=.03)
        meta = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        self.assertEqual(meta['profile'], KEY)
        self.assertEqual(meta['sample_kind'], 'synthetic')
        own = 'styles/architecture/blue-layered-icon-panels/1.0.0/example.svg'
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in selected['dependency_hashes'].items() if k != own and k not in mutable}
        self.assertEqual({k: meta['dependencies'][k] for k in frozen}, frozen)
        layers = [el for el in svg.iter() if el.get('data-layer')]
        self.assertEqual(len(layers), 4)
        layer_labels = [el for el in svg.iter() if el.get('data-layer-label')]
        self.assertEqual(len(layer_labels), 4)
        self.assertTrue(all(len([child for child in el if child.tag.endswith('tspan')]) == 4 for el in layer_labels))
        for role, count in (('decision-card', 3), ('analysis-card', 6), ('process-panel', 3), ('source-panel', 2)):
            self.assertEqual(len([el for el in svg.iter() if el.get('data-card') == role]), count)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-icon')]), 9)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-cell')]), 30)
        arrows = [el for el in svg.iter() if el.get('data-diagram-role') == 'connector']
        self.assertEqual(len(arrows), 4)
        self.assertTrue(all(el.get('d', '').rstrip().endswith('Z') for el in arrows))
        labels = {''.join(el.itertext()).strip() for el in svg.iter() if el.get('data-arrow-label')}
        self.assertEqual(labels, {edge['label'] for edge in meta['model']['edges']})
        self.assertTrue(all(el.get('data-qa-allow-overlap') == 'arrow-label' for el in svg.iter() if el.get('data-arrow-label')))
        self.assertEqual(len(meta['model']['edges']), 4)
        self.assertTrue(all(edge['source'] == '资源采集' and edge['target'] == '资源整理' for edge in meta['model']['edges']))
        self.assertFalse(any(el.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for el in svg.iter()))

    def test_preview_without_original(self):
        self.assertIn(KEY, self.catalog.read_catalog(ROOT)['style_numbers'].values())
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="AR-12"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')
        self.assertIn('ar12-title', card)


if __name__ == '__main__':
    unittest.main()
