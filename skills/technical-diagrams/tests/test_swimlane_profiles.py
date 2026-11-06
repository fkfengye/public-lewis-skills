import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]


class SwimlaneProfilesTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('swimlane_catalog', ROOT / 'scripts/catalog.py')
        self.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.catalog)

    def test_swimlane_presets_keep_line_selection_and_ordinary_default(self):
        expected = {'FC-03': 'soft-swimlanes', 'FC-04': 'contrast-swimlanes'}
        for number, style in expected.items():
            for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
                selected = self.catalog.resolve(ROOT, None, number=number, line_style=line)
                self.assertEqual(selected['key'], f'flowchart/{style}@1.0.0')
                self.assertEqual(selected['layout'], 'swimlane')
                self.assertEqual(selected['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'flowchart')['number'], 'FC-01')

    def test_swimlane_names_aliases_and_keys_resolve_consistently(self):
        examples = [('浅色分区泳道', 'FC-03'), ('浅色泳道', 'FC-03'),
                    ('深色标题泳道', 'FC-04'), ('高对比泳道', 'FC-04'),
                    ('flowchart/contrast-swimlanes@1.0.0', 'FC-04')]
        for name, number in examples:
            self.assertEqual(self.catalog.resolve(ROOT, 'flowchart', style=name)['number'], number)

    def test_swimlane_examples_are_synthetic_and_share_one_model(self):
        models = []
        namespaces = {'s': 'http://www.w3.org/2000/svg'}
        for number in ('FC-03', 'FC-04'):
            selected = self.catalog.resolve(ROOT, None, number=number)
            root = ET.parse(selected['example_path']).getroot()
            metadata = json.loads(root.find('s:metadata', namespaces).text)
            self.assertEqual(metadata['sample_kind'], 'synthetic')
            self.assertEqual(metadata['profile'], selected['key'])
            self.assertEqual(metadata['number'], number)
            self.assertEqual(metadata['line_style']['id'], 'rounded-orthogonal')
            models.append(metadata['model'])
            for tag in ('image', 'script', 'foreignObject'):
                self.assertFalse(root.findall(f'.//s:{tag}', namespaces))
            self.assertFalse(any('href' in key for element in root.iter() for key in element.attrib))
            self.assertTrue(root.findall('.//s:g[@role="list"]', namespaces))
        self.assertEqual(models[0], models[1])


if __name__ == '__main__':
    unittest.main()
