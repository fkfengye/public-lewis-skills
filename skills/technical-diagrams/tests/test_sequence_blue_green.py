import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class BlueGreenSequenceTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('catalog_sq03', ROOT / 'scripts/catalog.py')
        self.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.catalog)

    def test_selection_keeps_existing_defaults_and_lines(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            result = self.catalog.resolve(ROOT, None, number='SQ-03', line_style=line)
            self.assertEqual(result['key'], 'sequence/blue-green-phases@1.0.0')
            self.assertEqual(result['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'sequence', '蓝绿分阶段时序')['number'], 'SQ-03')
        self.assertEqual(self.catalog.resolve(ROOT, 'sequence')['number'], 'SQ-01')
        self.assertEqual(self.catalog.resolve(ROOT, None, number='SQ-02')['key'], 'sequence/classic-mono@1.0.0')

    def test_synthetic_example_models_and_renders_message_direction(self):
        result = self.catalog.resolve(ROOT, None, number='SQ-03')
        root = ET.parse(result['example_path']).getroot()
        metadata = json.loads(next(e for e in root.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual(metadata['sample_kind'], 'synthetic')
        self.assertEqual(metadata['profile'], result['key'])
        messages = metadata['model']['messages']
        paths = {e.attrib.get('id'): e for e in root.iter() if e.tag.endswith('path') and e.attrib.get('data-diagram-role') == 'connector'}
        self.assertEqual(len(paths), len(messages))
        for msg in messages:
            path = paths[msg['id']]
            coords = [int(v) for v in path.attrib['d'].replace('M', ' ').replace('H', ' ').split()]
            self.assertEqual(coords[0], metadata['model']['participants'][msg['from']])
            self.assertEqual(coords[2], metadata['model']['participants'][msg['to']])
            self.assertIn('marker-end', path.attrib)
            self.assertNotIn('marker-start', path.attrib)
            self.assertEqual('stroke-dasharray' in path.attrib, msg['kind'] == 'response')
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in root.iter()))
        self.assertFalse(any('href' in key for e in root.iter() for key in e.attrib))


if __name__ == '__main__':
    unittest.main()
