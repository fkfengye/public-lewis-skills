import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'flowchart/handdrawn-runtime-flow@1.0.0'


class RuntimeFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('fc08_catalog', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_selection_and_compatibility(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            resolved = self.catalog.resolve(ROOT, None, number='FC-08', line_style=line)
            self.assertEqual((resolved['key'], resolved['line_style']), (KEY, line))
        self.assertEqual(self.catalog.resolve(ROOT, 'flowchart')['number'], 'FC-01')
        self.assertEqual(self.catalog.resolve(ROOT, None, number='FC-07')['key'], 'flowchart/handdrawn-design-board@1.0.0')

    def test_example_semantics_and_visual_features(self):
        resolved = self.catalog.resolve(ROOT, None, number='FC-08')
        svg = ET.parse(resolved['example_path']).getroot()
        meta = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual((meta['profile'], meta['number'], meta['sample_kind']), (KEY, 'FC-08', 'synthetic'))
        self.assertEqual(meta['interaction_standard']['id'], 'single-direction')
        self.assertIn(meta['line_style']['id'], ('orthogonal', 'rounded-orthogonal', 'curved'))
        for dep in ('references/line-styles-v1.md', 'references/interaction-standards/1.0.0.md', 'references/interaction-standards/1.0.0.svg'):
            self.assertEqual(meta['dependencies'][dep], resolved['dependency_hashes'][dep])
        features = {e.get('data-feature') for e in svg.iter() if e.get('data-feature')}
        self.assertTrue({'main-boundary', 'external-boundary', 'actor', 'cloud', 'stack', 'pool', 'decision', 'worker-boundary', 'nested-grid', 'loop-annotation', 'exception-note'} <= features)
        edges = {e.get('id'): e for e in svg.iter() if e.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(edges), {e['id'] for e in meta['model']['connections']})
        for connection in meta['model']['connections']:
            route = connection['routing']
            self.assertTrue(route['alternatives'], connection['id'])
            self.assertEqual(route['crossings'], 0, connection['id'])
            self.assertTrue(all(route['bends'] <= option['bends'] for option in route['alternatives']), connection['id'])
        for edge in edges.values():
            self.assertIsNone(edge.get('marker-start'))
            self.assertIsNotNone(edge.get('marker-end'))
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in svg.iter()))

    def test_gallery_shows_authorized_original(self):
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="FC-08"', 1)[1].split('</article>', 1)[0]
        refs = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        self.assertEqual(refs[KEY], 'assets/reference-examples/fc-08-original.png')
        self.assertIn('查看原始样例图', card)
        original = (ROOT / refs[KEY]).read_bytes()
        embedded = card.split('data:image/png;base64,', 1)[1].split('"', 1)[0]
        self.assertEqual(base64.b64decode(embedded), original)

    def test_reference_details_have_actual_geometry(self):
        svg = ET.parse(ROOT / 'styles/flowchart/handdrawn-runtime-flow/1.0.0/example.svg').getroot()
        cloud = next(e for e in svg.iter() if e.get('data-feature') == 'cloud')
        cloud_layers = [e for e in cloud if e.get('data-cloud-layer')]
        self.assertEqual({e.get('data-cloud-layer') for e in cloud_layers}, {'shadow', 'body'})
        self.assertTrue(all(e.tag.endswith('path') for e in cloud_layers))
        styles = ''.join(e.text or '' for e in svg.iter() if e.tag.endswith('style'))
        self.assertIn('font-family:Virgil', styles)
        self.assertIn('font-family:Xiaolai', styles)
        self.assertIn('data:font/woff2;base64,', styles)
        edges = {e.get('id'): e for e in svg.iter() if e.get('data-diagram-role') == 'connector'}
        labels = {e.get('data-edge-label') for e in svg.iter() if e.get('data-edge-label')}
        for key in ('queue', 'dispatch', 'assign', 'send', 'archive'):
            self.assertIn(key, labels)
            self.assertGreaterEqual(edges[key].get('d').count('M'), 2, key)
            self.assertIsNotNone(edges[key].get('data-logical-path'))
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('mask', 'clipPath') for e in svg.iter()))


if __name__ == '__main__':
    unittest.main()
