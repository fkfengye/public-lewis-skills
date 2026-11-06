import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'flowchart/global-header-swimlanes@1.0.0'
EXAMPLE = 'styles/flowchart/global-header-swimlanes/1.0.0/example.svg'


class GlobalHeaderSwimlaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_fc06', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)
        cls.svg = ET.parse(ROOT / EXAMPLE).getroot()
        cls.meta = json.loads(next(e for e in cls.svg.iter() if e.tag.endswith('metadata')).text)

    def test_fixed_selection_and_independent_lines(self):
        resolved = self.catalog.resolve(ROOT, None, number='FC-06')
        self.assertEqual(resolved['key'], KEY)
        self.assertTrue(resolved['frozen'])
        hashes = dict(resolved['dependency_hashes'])
        hashes.pop(EXAMPLE)
        evolving = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        self.assertEqual({k: v for k, v in hashes.items() if k not in evolving},
                         {k: v for k, v in self.meta['dependencies'].items() if k not in evolving})
        self.assertEqual(self.catalog.resolve(ROOT, 'flowchart')['number'], 'FC-01')
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            self.assertEqual(self.catalog.resolve(ROOT, None, number='FC-06', line_style=line)['line_style'], line)

    def test_visible_structure_and_directed_flow(self):
        lanes = {e.get('data-lane') for e in self.svg.iter() if e.get('data-lane')}
        nodes = {e.get('data-node'): e for e in self.svg.iter() if e.get('data-node')}
        paths = {e.get('id'): e for e in self.svg.iter() if e.get('data-diagram-role') == 'connector'}
        model = self.meta['model']
        self.assertEqual(lanes, {lane['id'] for lane in model['lanes']})
        self.assertEqual(set(nodes), {n['id'] for n in model['nodes']})
        self.assertEqual(set(paths), {e['id'] for e in model['edges']})
        for node in model['nodes']:
            self.assertIn(node['owner'], lanes)
        for edge in model['edges']:
            self.assertIn(edge['source'], nodes)
            self.assertIn(edge['target'], nodes)
            self.assertEqual(paths[edge['id']].get('marker-end'), 'url(#arrow)')
        self.assertEqual(nodes['start'].get('fill'), '#4272C0')
        self.assertEqual(nodes['prepare'].get('fill'), '#D2DCE7')
        self.assertEqual(nodes['decision'].get('fill'), '#354865')
        self.assertEqual({e['condition'] for e in model['edges'] if 'condition' in e}, {'是', '否'})
        self.assertIn('V465', paths['e5'].get('d'))
        self.assertGreaterEqual(len([e for e in self.svg.iter() if e.tag.endswith('tspan')]), 2)
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in self.svg.iter()))

    def test_gallery_has_distinct_synthetic_example(self):
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf8')
        card = page.split('data-style-number="FC-06"', 1)[1].split('</article>', 1)[0]
        self.assertIn('资料受理与协作', card)
        self.assertIn('全局深蓝标题泳道', card)
        self.assertIn('查看原始样例图', card)
        refs = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf8'))
        original = base64.b64decode(card.split('data:image/png;base64,', 1)[1].split('"', 1)[0])
        self.assertEqual(original, (ROOT / refs[KEY]).read_bytes())


if __name__ == '__main__':
    unittest.main()
