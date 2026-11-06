import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class ContrastBandsTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('catalog_ar04', ROOT / 'scripts/catalog.py')
        self.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.catalog)

    def test_number_name_and_line_styles(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            result = self.catalog.resolve(ROOT, None, number='AR-04', line_style=line)
            self.assertEqual(result['key'], 'architecture/contrast-process-bands@1.0.0')
            self.assertEqual(result['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture', '暖底深绿分区')['number'], 'AR-04')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')

    def test_old_architecture_numbers_are_unchanged(self):
        expected = {'AR-01': 'architecture/soft-layered@1.0.0',
                    'AR-02': 'architecture/premium-cards@1.0.0',
                    'AR-03': 'architecture/layered-interactions@1.0.0'}
        for number, key in expected.items():
            self.assertEqual(self.catalog.resolve(ROOT, None, number=number)['key'], key)

    def test_example_is_synthetic_and_self_contained(self):
        result = self.catalog.resolve(ROOT, None, number='AR-04')
        svg = ET.parse(result['example_path']).getroot()
        metadata = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        self.assertEqual(metadata['sample_kind'], 'synthetic')
        self.assertEqual(metadata['profile'], result['key'])
        self.assertEqual(metadata['number'], 'AR-04')
        self.assertFalse(any(el.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for el in svg.iter()))
        self.assertFalse(any('href' in key for el in svg.iter() for key in el.attrib))


if __name__ == '__main__':
    unittest.main()
