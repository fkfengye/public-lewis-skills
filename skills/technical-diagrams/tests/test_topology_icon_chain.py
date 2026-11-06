import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
KEY = 'topology/icon-chain@1.0.0'


class TopologyIconChainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_topology', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_type_number_alias_and_line_options(self):
        data = self.catalog.read_catalog(ROOT)
        self.assertIn('topology', data['types'])
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            result = self.catalog.resolve(ROOT, None, number='TP-01', line_style=line)
            self.assertEqual(result['key'], KEY)
            self.assertEqual(result['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, '拓扑图')['key'], KEY)
        self.assertEqual(self.catalog.resolve(ROOT, 'topology', '橙红图标链路')['number'], 'TP-01')
        with self.assertRaises(ValueError):
            self.catalog.resolve(ROOT, 'flowchart', number='TP-01')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')

    def test_preview_contains_authorized_original_and_synthetic_model(self):
        data = self.catalog.read_catalog(ROOT)
        self.assertIn(KEY, data['style_numbers'].values())
        result = self.catalog.resolve(ROOT, None, number='TP-01')
        svg = ET.parse(result['example_path']).getroot()
        meta = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        self.assertEqual(meta['profile'], KEY)
        self.assertEqual(meta['sample_kind'], 'synthetic')
        self_file = 'styles/topology/icon-chain/1.0.0/example.svg'
        # 固定示例保留创建时的入口摘要；新增风格可授权更新入口文档。
        mutable_entry_docs = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in result['dependency_hashes'].items() if k != self_file and k not in mutable_entry_docs}
        self.assertEqual({k: meta['dependencies'][k] for k in frozen}, frozen)
        model = meta['model']
        self.assertTrue(all(e['source'] in model['nodes'] and e['target'] in model['nodes'] for e in model['edges']))
        self.assertTrue(any(sum(edge['source'] == node for edge in model['edges']) > 1 for node in model['nodes']), '通用模型应包含分支')
        labels = {''.join(el.itertext()).strip() for el in svg.iter() if el.tag.endswith('text')}
        self.assertTrue(set(model['nodes']).issubset(labels))
        paths = {el.get('id'): el for el in svg.iter() if el.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(paths), {edge['id'] for edge in model['edges']})
        self.assertTrue(all(el.get('marker-end') and not el.get('marker-start') for el in paths.values()))
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        original = (ROOT / index[KEY]).read_bytes()
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        self.assertIn('href="#type-topology"', page)
        card = page.split('data-style-number="TP-01"', 1)[1].split('</article>', 1)[0]
        self.assertIn('查看原始样例图', card)
        encoded = card.split('data:image/png;base64,', 1)[1].split('"', 1)[0]
        self.assertEqual(base64.b64decode(encoded), original)

    def test_gallery_displays_reference_style_features_separately(self):
        index = json.loads((ROOT / 'assets/gallery-examples/index.json').read_text(encoding='utf-8'))
        self.assertIn(KEY, index, 'TP-01 目录应展示原图特征图')
        path = ROOT / index[KEY]
        svg = ET.parse(path).getroot()
        meta = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        resolved = self.catalog.resolve(ROOT, None, number='TP-01')
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in resolved['dependency_hashes'].items() if k not in mutable}
        self.assertEqual({k: v for k, v in meta['dependencies'].items() if k not in mutable}, frozen)
        self.assertEqual(meta['profile'], KEY)
        self.assertAlmostEqual(float(svg.get('width')) / float(svg.get('height')), 1662 / 604, delta=.03)
        nodes = [el for el in svg.iter() if el.get('data-node')]
        self.assertEqual(len(nodes), 4)
        self.assertEqual(nodes[0].get('data-icon-kind'), nodes[2].get('data-icon-kind'))
        self.assertEqual(nodes[3].get('data-icon-kind'), 'storefront')
        self.assertEqual(len([el for el in svg.iter() if el.get('data-diagram-role') == 'connector']), 3)
        self.assertTrue(any(el.tag.endswith('tspan') for el in svg.iter()), '展示图应包含多行节点名称')
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="TP-01"', 1)[1].split('</article>', 1)[0]
        self.assertIn(path.read_text(encoding='utf-8'), card)
        self.assertIn('查看原始样例图', card)


if __name__ == '__main__':
    unittest.main()
