import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class BlueGreenGridTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('catalog_ar05', ROOT / 'scripts/catalog.py')
        self.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.catalog)

    def test_number_name_lines_and_existing_default(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            result = self.catalog.resolve(ROOT, None, number='AR-05', line_style=line)
            self.assertEqual(result['key'], 'architecture/blue-green-grid@1.0.0')
            self.assertEqual(result['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture', '蓝绿密集分区')['number'], 'AR-05')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        self.assertEqual(self.catalog.resolve(ROOT, None, number='AR-04')['key'], 'architecture/contrast-process-bands@1.0.0')

    def test_example_model_and_messages_are_self_contained(self):
        result = self.catalog.resolve(ROOT, None, number='AR-05')
        root = ET.parse(result['example_path']).getroot()
        metadata = json.loads(next(el for el in root.iter() if el.tag.endswith('metadata')).text)
        self.assertEqual(metadata['sample_kind'], 'synthetic')
        self.assertEqual(metadata['profile'], result['key'])
        edges = {e.attrib.get('id'): e for e in root.iter() if e.attrib.get('data-diagram-role') == 'connector'}
        parents = {child: parent for parent in root.iter() for child in parent}
        for edge in metadata['model']['edges']:
            path = edges[edge['id']]
            self.assertTrue(path.attrib.get('marker-end') or parents[path].attrib.get('marker-end'))
            self.assertNotIn('marker-start', path.attrib)
            self.assertEqual('stroke-dasharray' in path.attrib, edge['kind'] == 'response')
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in root.iter()))
        self.assertFalse(any('href' in key for e in root.iter() for key in e.attrib))


if __name__ == '__main__':
    unittest.main()
