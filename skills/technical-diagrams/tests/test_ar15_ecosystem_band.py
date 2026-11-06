import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
KEY = 'architecture/dual-ecosystem-capability-band@1.0.0'
EXAMPLE = 'styles/architecture/dual-ecosystem-capability-band/1.0.0/example.svg'


class AR15EcosystemBandTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_ar15', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)
        cls.svg = ET.parse(ROOT / EXAMPLE).getroot()
        cls.meta = json.loads(next(e for e in cls.svg.iter() if e.tag.endswith('metadata')).text)

    def test_resolves_number_and_all_independent_line_choices(self):
        resolved = self.catalog.resolve(ROOT, None, number='AR-15')
        self.assertEqual(resolved['key'], KEY)
        self.assertTrue(resolved['frozen'])
        dependencies = dict(resolved['dependency_hashes'])
        dependencies.pop(EXAMPLE)
        # 入口文档可随新增风格追加；固定示例中的摘要记录其创建时的入口版本。
        # 固定规范、语义、脚本等依赖仍必须与当前解析结果一致。
        evolving_entries = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        self.assertEqual({k: v for k, v in self.meta['dependencies'].items() if k not in evolving_entries},
                         {k: v for k, v in dependencies.items() if k not in evolving_entries})
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            self.assertEqual(self.catalog.resolve(ROOT, None, number='AR-15', line_style=line)['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')

    def test_visual_structure_and_model_agree(self):
        model = self.meta['model']
        nodes = {e.get('data-node') for e in self.svg.iter() if e.get('data-node')}
        self.assertEqual(nodes, {node['id'] for node in model['nodes']})
        connectors = {e.get('id').removeprefix('ar15-'): e for e in self.svg.iter()
                      if e.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(connectors), {edge['id'] for edge in model['edges']})
        for edge in model['edges']:
            self.assertIn(edge['source'], nodes, edge['id'])
            self.assertIn(edge['target'], nodes, edge['id'])
            self.assertTrue(connectors[edge['id']].get('marker-end'), edge['id'])
        groups = {e.get('data-capability-group') for e in self.svg.iter() if e.get('data-capability-group')}
        tabs = {e.get('data-title-tab') for e in self.svg.iter() if e.get('data-title-tab')}
        self.assertEqual(groups, {g['id'] for g in model['groups']})
        self.assertEqual(groups, tabs)
        self.assertEqual(len(groups), 6)
        icons = {e.get('data-icon') for e in self.svg.iter() if e.get('data-icon')}
        self.assertTrue({'relay-left', 'relay-right', 'lock', 'in-1', 'in-4', 'out-1', 'out-4'} <= icons)
        self.assertEqual(connectors['p4'].get('stroke-dasharray'), '1 11')
        self.assertEqual(connectors['p1'].get('stroke-dasharray'), '9 7')
        self.assertIn('L', connectors['f1'].get('d'))
        self.assertTrue(any(e.get('data-highlight') == 'true' for e in self.svg.iter()))
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in self.svg.iter()))

    def test_gallery_uses_independent_example_without_original(self):
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="AR-15"', 1)[1].split('</article>', 1)[0]
        self.assertIn('区域资源协作网络', card)
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')


if __name__ == '__main__':
    unittest.main()
