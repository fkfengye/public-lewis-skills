import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
KEY = 'architecture/three-column-feedback@1.0.0'


class ThreeColumnFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_ar09', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_selection_and_existing_defaults(self):
        data = self.catalog.read_catalog(ROOT)
        self.assertIn('AR-09', data['style_numbers'])
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            result = self.catalog.resolve(ROOT, None, number='AR-09', line_style=line)
            self.assertEqual(result['key'], KEY)
            self.assertEqual(result['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture', '三栏分区与反馈闭环')['number'], 'AR-09')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        self.assertEqual(self.catalog.resolve(ROOT, None, number='AR-08')['key'], 'architecture/cross-boundary-layers@1.0.0')

    def test_example_visually_covers_observed_structure(self):
        data = self.catalog.read_catalog(ROOT)
        self.assertIn(KEY, data['style_numbers'].values())
        selected = self.catalog.resolve(ROOT, None, number='AR-09')
        svg = ET.parse(selected['example_path']).getroot()
        meta = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        self.assertEqual(meta['profile'], KEY)
        self.assertEqual(meta['sample_kind'], 'synthetic')
        own = 'styles/architecture/three-column-feedback/1.0.0/example.svg'
        # 固定示例保留创建时的入口摘要；授权扩展可更新入口文档。
        mutable_entry_docs = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in selected['dependency_hashes'].items() if k != own and k not in mutable_entry_docs}
        self.assertEqual({k: meta['dependencies'][k] for k in frozen}, frozen)
        self.assertAlmostEqual(float(svg.get('width')) / float(svg.get('height')), 1680 / 708, delta=.03)
        groups = {el.get('data-group'): el for el in svg.iter() if el.get('data-group')}
        self.assertEqual(set(groups), {'input', 'matching', 'output'})
        self.assertTrue(groups['input'].get('stroke-dasharray'))
        self.assertTrue(groups['output'].get('stroke-dasharray'))
        self.assertFalse(groups['matching'].get('stroke-dasharray'))
        self.assertGreater(float(groups['matching'].get('rx')), 0)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-row')]), 5)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-match-card')]), 4)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-output-card')]), 4)
        connectors = [el for el in svg.iter() if el.get('data-diagram-role') == 'connector']
        self.assertEqual(len(connectors), 6)
        self.assertEqual(len(meta['model']['edges']), 6)
        self.assertTrue(all(el.get('marker-end') and not el.get('marker-start') for el in connectors))
        self.assertEqual(len([e for e in meta['model']['edges'] if e['kind'] == 'feedback']), 1)
        self.assertTrue(any('C' in el.get('d', '') for el in connectors))
        self.assertFalse(any(e['source'].startswith('匹配卡') and e['target'].startswith('匹配卡') for e in meta['model']['edges']))

    def test_authorized_original_is_embedded(self):
        data = self.catalog.read_catalog(ROOT)
        self.assertIn(KEY, data['style_numbers'].values())
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="AR-09"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')


if __name__ == '__main__':
    unittest.main()
