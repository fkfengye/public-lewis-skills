import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


class BlueGreenDetailedTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('catalog_ar06', ROOT / 'scripts/catalog.py')
        self.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.catalog)

    def test_independent_selection_and_old_defaults(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            selected = self.catalog.resolve(ROOT, None, number='AR-06', line_style=line)
            self.assertEqual(selected['key'], 'architecture/blue-green-detailed@1.0.0')
            self.assertEqual(selected['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture', '蓝绿密集细节')['number'], 'AR-06')
        self.assertEqual(self.catalog.resolve(ROOT, None, number='AR-05')['key'], 'architecture/blue-green-grid@1.0.0')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')

    def test_reference_visual_roles_and_example_are_self_contained(self):
        selected = self.catalog.resolve(ROOT, None, number='AR-06')
        tokens = json.loads(Path(selected['tokens_path']).read_text(encoding='utf-8'))
        for key in ('outer', 'module_blue', 'module_green', 'heading_blue', 'external_cyan', 'highlight_green', 'highlight_peach', 'dotted_border'):
            self.assertRegex(tokens['palette'][key], r'^#[0-9A-Fa-f]{6}$')
        svg = ET.parse(selected['example_path']).getroot()
        meta = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual(meta['sample_kind'], 'synthetic')
        self.assertEqual(meta['profile'], selected['key'])
        model = meta['model']
        self.assertTrue({'过滤配置', '来源目录', '展示配置'}.issubset(set(model['nodes'])))
        self.assertEqual(set(model['node_owners']), set(model['nodes']))
        visible_labels = {''.join(e.itertext()).strip() for e in svg.iter() if e.tag.endswith('text')}
        self.assertTrue(set(model['nodes']).issubset(visible_labels))
        self.assertEqual(len(model['edges']), 10)
        self.assertTrue(all(edge.get('label') for edge in model['edges']))
        paths = {e.attrib.get('id'): e for e in svg.iter() if e.attrib.get('data-diagram-role') == 'connector'}
        parents = {child: parent for parent in svg.iter() for child in parent}
        for edge in meta['model']['edges']:
            path = paths[edge['id']]
            self.assertTrue(path.attrib.get('marker-end') or parents[path].attrib.get('marker-end'))
            self.assertNotIn('marker-start', path.attrib)
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in svg.iter()))
        self.assertFalse(any('href' in key for e in svg.iter() for key in e.attrib))


if __name__ == '__main__':
    unittest.main()
