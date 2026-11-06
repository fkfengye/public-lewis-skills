import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'architecture/cross-boundary-layers@1.0.0'


class CrossBoundaryLayersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_ar08', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_selection_and_previous_profiles(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            result = self.catalog.resolve(ROOT, None, number='AR-08', line_style=line)
            self.assertEqual(result['key'], KEY)
            self.assertEqual(result['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture', '跨域分层交互')['number'], 'AR-08')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        self.assertEqual(self.catalog.resolve(ROOT, None, number='AR-07')['key'], 'architecture/ecosystem-capability-matrix@1.0.0')

    def test_synthetic_model_and_visual_roles(self):
        result = self.catalog.resolve(ROOT, None, number='AR-08')
        tokens = json.loads(Path(result['tokens_path']).read_text(encoding='utf-8'))
        for role in ('heading', 'clearing', 'group_peach', 'processing', 'edge', 'node_border'):
            self.assertRegex(tokens['palette'][role], r'^#[0-9A-Fa-f]{6}$')
        svg = ET.parse(result['example_path']).getroot()
        self.assertEqual(svg.get('aria-labelledby'), 'ar08-title ar08-desc')
        meta = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        self.assertEqual(meta['profile'], KEY)
        self.assertEqual(meta['sample_kind'], 'synthetic')
        model = meta['model']
        self.assertEqual(set(model['nodes']), set(model['node_owners']))
        self.assertTrue(all(edge['source'] in model['nodes'] and edge['target'] in model['nodes'] and edge['label'] for edge in model['edges']))
        labels = {''.join(el.itertext()).strip() for el in svg.iter() if el.tag.endswith('text')}
        self.assertTrue(set(model['nodes']).issubset(labels))
        self.assertTrue({edge['label'] for edge in model['edges']}.issubset(labels))
        paths = {el.get('id'): el for el in svg.iter() if el.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(paths), {edge['id'] for edge in model['edges']})
        self.assertTrue(all(el.get('marker-end') and not el.get('marker-start') for el in paths.values()))
        self.assertFalse(any(el.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for el in svg.iter()))
        self.assertFalse(any('href' in key for el in svg.iter() for key in el.attrib))

    def test_original_reference_embedded_in_own_card(self):
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="AR-08"', 1)[1].split('</article>', 1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')

    def test_feature_atlas_preserves_five_layers_and_model_relations(self):
        svg = ET.parse(ROOT / 'styles/architecture/cross-boundary-layers/1.0.0/feature-atlas.svg').getroot()
        meta = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        model = meta['model']
        self.assertEqual(meta['profile'], KEY)
        selected = self.catalog.resolve(ROOT, None, number='AR-08')
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in selected['dependency_hashes'].items() if k not in mutable}
        self.assertEqual({k: meta['dependencies'][k] for k in frozen}, frozen)
        reference = ROOT / 'styles/architecture/cross-boundary-layers/1.0.0/reference-analysis.md'
        self.assertEqual(len(model['layers']), 5)
        self.assertTrue({'甲侧资源', '甲侧节点', '甲侧终点', '乙侧节点', '乙侧终点', '乙侧资源'}.issubset(model['nodes']))
        self.assertEqual(set(model['nodes']), set(model['node_owners']))
        labels = {''.join(el.itertext()).strip() for el in svg.iter() if el.tag.endswith('text')}
        self.assertTrue(set(model['nodes']).issubset(labels))
        self.assertTrue({edge['label'] for edge in model['edges']}.issubset(labels))
        paths = {el.get('id'): el for el in svg.iter() if el.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(paths), {edge['id'] for edge in model['edges']})
        self.assertTrue(all(el.get('marker-end') and not el.get('marker-start') for el in paths.values()))
        self.assertTrue(any(el.get('stroke-dasharray') and el.get('stroke') == '#26303A' for el in paths.values()))
        self.assertTrue(any(el.get('stroke-dasharray') and el.get('stroke-linecap') == 'round' for el in paths.values()))
        requests = {(edge['source'], edge['target']) for edge in model['edges'] if edge['kind'] == 'request'}
        for edge in model['edges']:
            if edge['kind'] == 'response':
                self.assertIn((edge['target'], edge['source']), requests)


if __name__ == '__main__':
    unittest.main()
