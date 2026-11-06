import base64
import json
import re
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'architecture/contrast-process-bands@1.0.0'
ATLAS = 'styles/architecture/contrast-process-bands/1.0.0/feature-atlas.svg'


class AR04FeatureGalleryTests(unittest.TestCase):
    def test_rounded_connectors_follow_recorded_routes(self):
        svg = ET.parse(ROOT / ATLAS).getroot()
        meta = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual(meta['line_style']['id'], 'rounded-orthogonal')
        paths = {e.get('id'): e.get('d') for e in svg.iter() if e.get('data-diagram-role') == 'connector'}
        for edge in meta['model']['edges']:
            controls = {(float(x), float(y)) for x, y in re.findall(r'Q\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)', paths[edge['id']])}
            for a, b, c in zip(edge['points'], edge['points'][1:], edge['points'][2:]):
                if (b[0]-a[0])*(c[1]-b[1]) != (b[1]-a[1])*(c[0]-b[0]):
                    self.assertIn(tuple(b), controls, (edge['id'], '转角缺少真实圆角', b))
            self.assertGreaterEqual(len(controls), edge['crossing_bridges'])
        for control in ('Q1086 1555', 'Q1250 1606', 'Q2120 1606', 'Q2370 1606'):
            self.assertIn(control, paths['ar04-atlas-record-1'])
        self.assertIn('Q1265 1555', paths['ar04-atlas-e14'])

    def test_connector_endpoints_reach_node_boundaries(self):
        svg = ET.parse(ROOT / ATLAS).getroot()
        meta = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        nodes = {n['id']: n for n in meta['model']['nodes']}
        for edge in meta['model']['edges']:
            for role, point in (('source', edge['points'][0]), ('target', edge['points'][-1])):
                node = nodes[edge[role]]
                x, y, w, h = node['bounds']
                px, py = point
                self.assertTrue(x - 2 <= px <= x + w + 2 and y - 2 <= py <= y + h + 2,
                                (edge['id'], role, node['id'], point))
                self.assertLessEqual(min(abs(px-x), abs(px-x-w), abs(py-y), abs(py-y-h)), 2,
                                     (edge['id'], role, node['id'], point))

    def test_gallery_shows_complete_feature_atlas_and_authorized_original(self):
        index = json.loads((ROOT / 'assets/gallery-examples/index.json').read_text(encoding='utf-8'))
        self.assertEqual(index.get(KEY), ATLAS)
        svg = ET.parse(ROOT / ATLAS).getroot()
        meta = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual(meta['profile'], KEY)
        self.assertEqual(meta['sample_kind'], 'synthetic-feature-atlas')
        roles = [e.get('data-feature') for e in svg.iter()]
        for role, minimum in {'event-card': 6, 'platform-card': 5, 'skill-tag': 7,
                              'executor-card': 3, 'decision': 4, 'record-cylinder': 6,
                              'legend-item': 4, 'message-child': 2}.items():
            self.assertGreaterEqual(roles.count(role), minimum, role)
        nodes = {e.get('data-node') for e in svg.iter() if e.get('data-node')}
        self.assertEqual(nodes, {n['id'] for n in meta['model']['nodes']})
        edges = {e.get('id') for e in svg.iter() if e.get('data-diagram-role') == 'connector'}
        self.assertEqual(edges, {e['id'] for e in meta['model']['edges']})
        self.assertTrue(all(e['source'] in nodes and e['target'] in nodes for e in meta['model']['edges']))
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="AR-04"', 1)[1].split('</article>', 1)[0]
        self.assertIn('ar04-atlas', card)
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')


if __name__ == '__main__':
    unittest.main()
