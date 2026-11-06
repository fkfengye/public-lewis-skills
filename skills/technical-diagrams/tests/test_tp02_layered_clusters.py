import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'topology/layered-service-clusters@1.0.0'
EXAMPLE = 'styles/topology/layered-service-clusters/1.0.0/example.svg'


class LayeredClustersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('tp02_catalog', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)
        cls.svg = ET.parse(ROOT / EXAMPLE).getroot()
        cls.meta = json.loads(next(e for e in cls.svg.iter() if e.tag.endswith('metadata')).text)

    def test_resolution_and_dependencies(self):
        resolved = self.catalog.resolve(ROOT, None, number='TP-02')
        self.assertEqual(resolved['key'], KEY)
        self.assertTrue(resolved['frozen'])
        deps = dict(resolved['dependency_hashes'])
        deps.pop(EXAMPLE)
        evolving = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        self.assertEqual({k: v for k, v in self.meta['dependencies'].items() if k not in evolving},
                         {k: v for k, v in deps.items() if k not in evolving})
        self.assertEqual(self.catalog.resolve(ROOT, 'topology')['number'], 'TP-01')
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            self.assertEqual(self.catalog.resolve(ROOT, None, number='TP-02', line_style=line)['line_style'], line)

    def test_structure_and_connections(self):
        model = self.meta['model']
        nodes = {e.get('data-node') for e in self.svg.iter() if e.get('data-node')}
        self.assertEqual(nodes, {n['id'] for n in model['nodes']})
        paths = {e.get('id'): e for e in self.svg.iter() if e.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(paths), {e['id'] for e in model['edges']})
        for edge in model['edges']:
            self.assertIn(edge['source'], nodes)
            self.assertIn(edge['target'], nodes)
            self.assertEqual(paths[edge['id']].get('marker-end'), 'url(#arrow)')
        self.assertEqual(paths['e8'].get('stroke-dasharray'), '7 5')
        self.assertEqual({e.get('data-visual-group') for e in self.svg.iter() if e.get('data-visual-group')}, {'operations', 'resources'})
        self.assertEqual(model['replicas'], {'entry': 2, 'gateway': 3, 'work-a': 2, 'work-b': 2, 'work-c': 2})
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in self.svg.iter()))

    def test_independent_preview_without_original(self):
        card = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf8').split('data-style-number="TP-02"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')
        self.assertIn('分布式内容协作拓扑', card)
        self.assertIn('特征展示', card)
        for name in ('ProcessOn', 'Nginx', 'Feign', 'Ribbon'):
            self.assertNotIn(name, (ROOT / EXAMPLE).read_text(encoding='utf8'))

    def test_gallery_atlas_exposes_full_feature_set(self):
        index = json.loads((ROOT / 'assets/gallery-examples/index.json').read_text(encoding='utf8'))
        svg = ET.parse(ROOT / index[KEY]).getroot()
        meta = json.loads(next(e for e in svg if e.tag.endswith('metadata')).text)
        self.assertEqual(meta['sample_kind'], 'synthetic-feature-atlas')
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = self.catalog.resolve(ROOT, None, number='TP-02')['dependency_hashes']
        self.assertEqual({k: v for k, v in meta['dependencies'].items() if k not in mutable},
                         {k: v for k, v in frozen.items() if k not in mutable})
        self.assertEqual(len([e for e in svg.iter() if e.get('data-replica')]), 9)
        self.assertEqual(len([e for e in svg.iter() if e.get('data-entry-icon')]), 2)
        panels = [e for e in svg.iter() if e.tag.endswith('rect') and e.get('fill') == '#FFFFFF'
                  and e.get('width') in {'500', '1330', '170'}]
        self.assertEqual(len(panels), 4)
        self.assertTrue(all(e.get('stroke') == '#30363A' for e in panels))
        tokens = json.loads((ROOT / 'styles/topology/layered-service-clusters/1.0.0/tokens.json').read_text(encoding='utf8'))
        self.assertEqual(tokens['palette']['panel_border'], '#30363A')
        paths = {e.get('id'): e for e in svg.iter() if e.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(paths), {e['id'] for e in meta['model']['edges']})
        self.assertEqual(paths['e21'].get('marker-end'), 'url(#arrow-open)')
        self.assertEqual(paths['e20'].get('stroke-dasharray'), '7 5')


if __name__ == '__main__':
    unittest.main()
