import base64
import importlib.util
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'sequence/handdrawn-pastel-branches@1.0.0'
SVG = ROOT / 'styles/sequence/handdrawn-pastel-branches/1.0.0/example.svg'


class HanddrawnPastelSequenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('sq05_catalog', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_resolution_and_old_sequence_semantics(self):
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            result = self.catalog.resolve(ROOT, None, number='SQ-05', line_style=line)
            self.assertEqual((result['key'], result['line_style'], result['semantic_version']), (KEY, line, '1.1.0'))
        self.assertEqual(self.catalog.resolve(ROOT, 'sequence')['number'], 'SQ-01')
        for number in ('SQ-01', 'SQ-02', 'SQ-03', 'SQ-04'):
            self.assertEqual(self.catalog.resolve(ROOT, None, number=number)['semantic_version'], '1.0.0')
        old = (ROOT / 'types/sequence/1.0.0.md').read_text(encoding='utf-8').strip().split('\n\n')
        new = (ROOT / 'types/sequence/1.1.0.md').read_text(encoding='utf-8').strip().split('\n\n')
        self.assertEqual(old[1:4], new[1:4])
        self.assertEqual(old[-1], new[-1])
        self.assertNotEqual(old[4], new[4])

    def test_model_and_visible_sequence(self):
        root = ET.parse(SVG).getroot()
        meta = json.loads(next(e for e in root.iter() if e.tag.endswith('metadata')).text)
        self.assertEqual((meta['profile'], meta['number'], meta['semantic_version'], meta['sample_kind']),
                         (KEY, 'SQ-05', '1.1.0', 'synthetic'))
        participants = {p['id']: p for p in meta['model']['participants']}
        self.assertEqual({e.get('data-participant') for e in root.iter() if e.get('data-participant')}, set(participants))
        self.assertEqual({e.get('data-lifeline') for e in root.iter() if e.get('data-lifeline')}, set(participants))
        for item in root.iter():
            pid = item.get('data-lifeline')
            if pid:
                self.assertEqual(item.get('d'), f'M{participants[pid]["x"]} 455 V1475')
        features = {e.get('data-feature') for e in root.iter() if e.get('data-feature')}
        self.assertTrue({'panel','actor','title-underline','title-icon','margin-note','fragment','fragment-tab','branch-divider'} <= features)
        self.assertGreaterEqual(sum(1 for e in root.iter() if e.get('data-activation')), 4)
        self.assertEqual({e.get('data-guard') for e in root.iter() if e.get('data-guard')}, {'accept', 'revise'})
        messages = meta['model']['messages']
        paths = {e.get('id'):e for e in root.iter() if e.get('data-diagram-role') == 'connector'}
        self.assertEqual(set(paths), {m['id'] for m in messages})
        self.assertTrue(any(m['branch'] == 'accept' for m in messages))
        self.assertTrue(any(m['branch'] == 'revise' for m in messages))
        self.assertTrue(any(m['branch'] is None for m in messages))
        self.assertTrue(any(m.get('lines', 1) > 1 for m in messages))
        for message in messages:
            path = paths[message['id']]
            self.assertIsNone(path.get('marker-start'))
            self.assertIsNotNone(path.get('marker-end'))
            self.assertGreaterEqual(path.get('d').count('M'), 2, message['id'])
            commands = re.findall(r'[A-Za-z]', path.get('d'))
            self.assertTrue(set(commands) <= {'M','H'}, message['id'])
            pieces = re.findall(r'M\s*([\d.]+)\s+([\d.]+)\s+H\s*([\d.]+)', path.get('d'))
            self.assertEqual(len(pieces), 2, message['id'])
            self.assertEqual(float(pieces[0][0]), message['source_x'], message['id'])
            self.assertEqual(float(pieces[-1][2]), message['target_x'], message['id'])
            self.assertTrue(all(float(piece[1]) == message['y'] for piece in pieces), message['id'])
            self.assertEqual(path.get('data-logical-path'),
                             f'M {message["source_x"]} {message["y"]} H {message["target_x"]}')
            sign = 1 if participants[message['target']]['x'] > participants[message['source']]['x'] else -1
            expected_source = participants[message['source']]['x'] + (5 * sign if message['source'] != 'editor' else 0)
            expected_target = participants[message['target']]['x'] - (5 * sign if message['target'] != 'editor' else 0)
            self.assertEqual((message['source_x'], message['target_x']), (expected_source, expected_target), message['id'])
            if message['role'] == 'response':
                self.assertEqual(path.get('stroke-dasharray'), '8 6')
            else:
                self.assertIsNone(path.get('stroke-dasharray'))
        self.assertFalse(any(e.tag.rsplit('}',1)[-1] in ('image','script','foreignObject','mask') for e in root.iter()))

    def test_original_and_synthetic_preview_are_distinct(self):
        refs = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        card = page.split('data-style-number="SQ-05"',1)[1].split('</article>',1)[0]
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')
        text = SVG.read_text(encoding='utf-8')
        self.assertNotIn('Online Store', text)
        self.assertNotIn('Payment Gateway', text)


if __name__ == '__main__':
    unittest.main()
