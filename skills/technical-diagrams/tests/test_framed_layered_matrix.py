import base64
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'architecture/framed-layered-matrix@1.0.0'


class FramedLayeredMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_ar13', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_selection_and_existing_defaults(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            resolved = self.catalog.resolve(ROOT, None, number='AR-13', line_style=line)
            self.assertEqual((resolved['key'], resolved['line_style']), (KEY, line))
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture', '侧栏保障分层矩阵')['number'], 'AR-13')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        self.assertEqual(self.catalog.resolve(ROOT, 'timeline')['number'], 'TL-01')

    def test_transparent_reference_does_not_become_black_canvas(self):
        selected = self.catalog.resolve(ROOT, None, number='AR-13')
        svg = ET.parse(selected['example_path']).getroot()
        canvas = next(e for e in svg if e.tag.endswith('rect'))
        self.assertEqual(canvas.get('fill'), '#FFFFFF')
        tokens = json.loads(Path(selected['tokens_path']).read_text(encoding='utf-8'))
        self.assertEqual(tokens['palette']['canvas'], '#FFFFFF')

    def test_example_represents_source_features_without_invented_links(self):
        selected = self.catalog.resolve(ROOT, None, number='AR-13')
        svg = ET.parse(selected['example_path']).getroot()
        self.assertAlmostEqual(float(svg.get('width')) / float(svg.get('height')), 2038 / 1829, delta=.02)
        meta = json.loads(next(e for e in svg.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual((meta['profile'], meta['sample_kind']), (KEY, 'synthetic'))
        self.assertEqual(meta['model']['edges'], [])
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        own = 'styles/architecture/framed-layered-matrix/1.0.0/example.svg'
        frozen = {k: v for k, v in selected['dependency_hashes'].items() if k not in mutable | {own}}
        self.assertEqual({k: meta['dependencies'][k] for k in frozen}, frozen)
        self.assertEqual(len([e for e in svg.iter() if e.get('data-layer')]), 6)
        self.assertEqual({e.get('data-guardrail') for e in svg.iter() if e.get('data-guardrail')},
                         {'left', 'right', 'bottom'})
        self.assertEqual(len([e for e in svg.iter() if e.get('data-app-group')]), 3)
        self.assertEqual(len([e for e in svg.iter() if e.get('data-node') == 'application']), 21)
        self.assertEqual({e.get('data-service-group') for e in svg.iter() if e.get('data-service-group')},
                         {'core', 'support'})
        for kind, count in [('spanning-core', 1), ('core', 8), ('support', 10), ('side', 5),
                            ('application-service', 7), ('infrastructure', 3)]:
            self.assertEqual(len([e for e in svg.iter() if e.get('data-node') == kind]), count)
        self.assertEqual(len([e for e in svg.iter() if e.get('data-capability-sidebar')]), 1)
        self.assertEqual(len([e for e in svg.iter() if e.get('data-storage')]), 3)
        self.assertEqual(len([e for e in svg.iter() if e.get('data-placeholder')]), 1)
        self.assertEqual(meta['model']['layers']['data_placeholder'], '…')
        self.assertFalse(any(e.get('data-diagram-role') == 'connector' for e in svg.iter()))
        self.assertFalse(any(e.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for e in svg.iter()))

    def test_original_available_separately_from_synthetic_preview(self):
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        original = (ROOT / index[KEY]).read_bytes()
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="AR-13"', 1)[1].split('</article>', 1)[0]
        self.assertIn('查看原始样例图', card)
        self.assertEqual(base64.b64decode(card.split('data:image/png;base64,', 1)[1].split('"', 1)[0]), original)
        self.assertIn('ar13-title', card)


if __name__ == '__main__':
    unittest.main()
