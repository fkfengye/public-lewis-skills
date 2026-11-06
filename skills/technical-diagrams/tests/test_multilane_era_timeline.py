import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'timeline/multilane-era-axis@1.0.0'


class MultilaneEraTimelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_tl02', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_selection_and_existing_defaults(self):
        self.assertIn('TL-02', self.catalog.read_catalog(ROOT)['style_numbers'])
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            selected = self.catalog.resolve(ROOT, None, number='TL-02', line_style=line)
            self.assertEqual(selected['key'], KEY)
            self.assertEqual(selected['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, '时间线图', '多层时期事件时间轴')['number'], 'TL-02')
        self.assertEqual(self.catalog.resolve(ROOT, 'timeline')['number'], 'TL-01')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')

    def test_visual_layers_and_proportional_model(self):
        self.assertIn(KEY, self.catalog.read_catalog(ROOT)['style_numbers'].values())
        selected = self.catalog.resolve(ROOT, None, number='TL-02')
        svg = ET.parse(selected['example_path']).getroot()
        self.assertAlmostEqual(float(svg.get('width')) / float(svg.get('height')), 1323 / 660, delta=.03)
        meta = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        self.assertEqual(meta['profile'], KEY)
        self.assertEqual(meta['sample_kind'], 'synthetic')
        own = 'styles/timeline/multilane-era-axis/1.0.0/example.svg'
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in selected['dependency_hashes'].items() if k != own and k not in mutable}
        self.assertEqual({k: meta['dependencies'][k] for k in frozen}, frozen)
        model = meta['model']
        self.assertEqual(model['scale'], 'proportional')
        self.assertEqual(len([el for el in svg.iter() if el.get('data-lane')]), 3)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-top-bracket')]), 3)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-major-period')]), 5)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-sub-period')]), 4)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-bottom-period')]), 4)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-brace')]), 4)
        events = [el for el in svg.iter() if el.get('data-event')]
        self.assertEqual(len(events), len(model['events']))
        self.assertGreaterEqual(len(events), 16)
        self.assertEqual([e['year'] for e in model['events']], sorted(e['year'] for e in model['events']))
        labels = {''.join(el.itertext()).strip() for el in svg.iter() if el.tag.endswith('text')}
        self.assertTrue({e['title'] for e in model['events']}.issubset(labels))
        self.assertTrue({str(e['year']) for e in model['events']}.issubset(labels))
        for group, event in zip(events, model['events']):
            self.assertEqual(group.get('data-year'), str(event['year']))
            tick = next(el for el in group if el.get('data-tick'))
            self.assertEqual(float(tick.get('x1')), 160 + 38 * (event['year'] - 1980))
            self.assertEqual(tick.get('x1'), tick.get('x2'))
            self.assertTrue(any(el.get('data-diamond') for el in group))
        spans = {el.get('data-span'): el for el in svg.iter() if el.get('data-span')}
        self.assertEqual(set(spans), {item['id'] for item in model['spans']})
        for item in model['spans']:
            el = spans[item['id']]
            self.assertEqual(int(el.get('data-start')), item['start'])
            self.assertEqual(int(el.get('data-end')), item['end'])
            self.assertEqual(float(el.get('x1')), 160 + 38 * (item['start'] - 1980))
            self.assertEqual(float(el.get('x2')), 160 + 38 * (item['end'] - 1980))
        self.assertTrue(any(el.get('data-axis') for el in svg.iter()))

    def test_authorized_original_and_preview(self):
        self.assertIn(KEY, self.catalog.read_catalog(ROOT)['style_numbers'].values())
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="TL-02"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')
        self.assertIn('tl02-title', card)


if __name__ == '__main__':
    unittest.main()
