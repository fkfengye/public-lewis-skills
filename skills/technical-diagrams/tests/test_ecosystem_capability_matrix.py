import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'architecture/ecosystem-capability-matrix@1.0.0'


class EcosystemCapabilityMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_ar07', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_number_name_lines_and_old_defaults(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            selected = self.catalog.resolve(ROOT, None, number='AR-07', line_style=line)
            self.assertEqual(selected['key'], KEY)
            self.assertEqual(selected['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture', '蓝粉生态能力矩阵')['number'], 'AR-07')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        self.assertEqual(self.catalog.resolve(ROOT, None, number='AR-06')['key'], 'architecture/blue-green-detailed@1.0.0')

    def test_tokens_and_synthetic_example_have_consistent_model(self):
        selected = self.catalog.resolve(ROOT, None, number='AR-07')
        tokens = json.loads(Path(selected['tokens_path']).read_text(encoding='utf-8'))
        for role in ('ecosystem', 'platform', 'network', 'accent', 'card', 'heading_blue'):
            self.assertRegex(tokens['palette'][role], r'^#[0-9A-Fa-f]{6}$')
        svg = ET.parse(selected['example_path']).getroot()
        meta = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        self.assertEqual(meta['sample_kind'], 'synthetic')
        self.assertEqual(meta['profile'], KEY)
        model = meta['model']
        self.assertEqual(set(model['nodes']), set(model['node_owners']))
        self.assertTrue(all(edge['source'] in model['nodes'] and edge['target'] in model['nodes'] and edge['label'] for edge in model['edges']))
        labels = {''.join(el.itertext()).strip() for el in svg.iter() if el.tag.endswith('text')}
        self.assertTrue(set(model['nodes']).issubset(labels))
        paths = {el.get('id'): el for el in svg.iter() if el.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(paths), {edge['id'] for edge in model['edges']})
        self.assertTrue(all(el.get('marker-end') and not el.get('marker-start') for el in paths.values()))
        self.assertTrue({edge['label'] for edge in model['edges']}.issubset(labels))
        gradients = [el for el in svg.iter() if el.tag.endswith('linearGradient')]
        self.assertTrue(gradients)
        self.assertTrue(all(el.get('gradientUnits') == 'userSpaceOnUse' for el in gradients))
        self.assertFalse(any(el.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for el in svg.iter()))
        self.assertFalse(any('href' in key for el in svg.iter() for key in el.attrib))
        content = Path(selected['example_path']).read_text(encoding='utf-8')
        self.assertNotIn('WorldFirst', content)
        self.assertNotIn('万里汇', content)

    def test_authorized_original_is_in_its_card(self):
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="AR-07"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')


if __name__ == '__main__':
    unittest.main()
