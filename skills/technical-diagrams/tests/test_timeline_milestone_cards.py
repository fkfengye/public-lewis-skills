import base64
import importlib.util
import json
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
KEY = 'timeline/color-milestone-cards@1.0.0'


class TimelineMilestoneCardsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('catalog_timeline', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_new_type_number_aliases_and_line_options(self):
        data = self.catalog.read_catalog(ROOT)
        self.assertIn('timeline', data['types'])
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            selected = self.catalog.resolve(ROOT, None, number='TL-01', line_style=line)
            self.assertEqual(selected['key'], KEY)
            self.assertEqual(selected['line_style'], line)
        self.assertEqual(self.catalog.resolve(ROOT, '时间线图')['key'], KEY)
        self.assertEqual(self.catalog.resolve(ROOT, 'timeline', '彩色里程碑卡片')['number'], 'TL-01')
        with self.assertRaises(ValueError):
            self.catalog.resolve(ROOT, 'sequence', number='TL-01')
        self.assertEqual(self.catalog.resolve(ROOT, 'architecture')['number'], 'AR-01')
        self.assertEqual(self.catalog.resolve(ROOT, 'topology')['number'], 'TP-01')

    def test_example_preserves_milestone_visuals_and_time_order(self):
        self.assertIn(KEY, self.catalog.read_catalog(ROOT)['style_numbers'].values())
        selected = self.catalog.resolve(ROOT, None, number='TL-01')
        svg = ET.parse(selected['example_path']).getroot()
        self.assertAlmostEqual(float(svg.get('width')) / float(svg.get('height')), 1850 / 654, delta=.03)
        meta = json.loads(next(el for el in svg.iter() if el.tag.endswith('metadata')).text)
        self.assertEqual(meta['profile'], KEY)
        self.assertEqual(meta['sample_kind'], 'synthetic')
        own = 'styles/timeline/color-milestone-cards/1.0.0/example.svg'
        mutable = {'SKILL.md', 'scripts/catalog.py', 'references/extensions-v1.md', 'references/style-numbering-v1.md'}
        frozen = {k: v for k, v in selected['dependency_hashes'].items() if k != own and k not in mutable}
        self.assertEqual({k: meta['dependencies'][k] for k in frozen}, frozen)
        events = meta['model']['events']
        self.assertEqual(len(events), 6)
        self.assertEqual([e['date'] for e in events], sorted(e['date'] for e in events))
        milestones = [el for el in svg.iter() if el.get('data-milestone')]
        self.assertEqual(len(milestones), 6)
        self.assertEqual([el.get('data-date') for el in milestones], [e['date'] for e in events])
        positions = [int(re.fullmatch(r'translate\((\d+) 0\)', el.get('transform')).group(1)) for el in milestones]
        self.assertEqual(len(set(b - a for a, b in zip(positions, positions[1:]))), 1)
        self.assertEqual(len(set(int(b['date']) - int(a['date']) for a, b in zip(events, events[1:]))), 1)
        for group in milestones:
            core = next(el for el in group.iter() if el.get('data-core'))
            stem = next(el for el in group.iter() if el.get('data-stem'))
            card = next(el for el in group.iter() if el.get('data-card'))
            header = next(el for el in group.iter() if el.get('data-header'))
            self.assertEqual({core.get('fill'), stem.get('stroke'), card.get('stroke'), header.get('fill')}, {core.get('fill')})
        self.assertEqual(len([el for el in svg.iter() if el.get('data-halo')]), 6)
        self.assertEqual(len([el for el in svg.iter() if el.get('data-core')]), 6)
        stems = [el for el in svg.iter() if el.get('data-stem')]
        self.assertEqual(len(stems), 6)
        self.assertTrue(all(el.get('stroke-dasharray') and not el.get('marker-end') for el in stems))
        cards = [el for el in svg.iter() if el.get('data-card')]
        self.assertEqual(len(cards), 6)
        self.assertTrue(all(float(el.get('rx')) > 0 for el in cards))
        self.assertEqual(len([el for el in svg.iter() if el.get('data-header')]), 6)
        axis = next(el for el in svg.iter() if el.get('data-axis'))
        self.assertTrue(axis.get('marker-end'))
        labels = {''.join(el.itertext()).strip() for el in svg.iter() if el.tag.endswith('text')}
        self.assertTrue({e['date'] for e in events}.issubset(labels))
        self.assertTrue({e['title'] for e in events}.issubset(labels))

    def test_authorized_original_and_preview(self):
        self.assertIn(KEY, self.catalog.read_catalog(ROOT)['style_numbers'].values())
        index = json.loads((ROOT / 'assets/reference-examples/index.json').read_text(encoding='utf-8'))
        original = (ROOT / index[KEY]).read_bytes()
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf-8')
        self.assertIn('href="#type-timeline"', page)
        card = page.split('data-style-number="TL-01"', 1)[1].split('</article>', 1)[0]
        self.assertIn('查看原始样例图', card)
        self.assertEqual(base64.b64decode(card.split('data:image/png;base64,', 1)[1].split('"', 1)[0]), original)
        self.assertIn('tl01-title', card)


if __name__ == '__main__':
    unittest.main()
