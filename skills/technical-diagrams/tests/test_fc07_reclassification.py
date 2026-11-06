import base64
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
OLD = 'architecture/handdrawn-design-board@1.0.0'
NEW = 'flowchart/handdrawn-design-board@1.0.0'


class HanddrawnFlowchartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('fc07_catalog', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def test_new_flowchart_and_old_compatibility(self):
        new = self.catalog.resolve(ROOT, None, number='FC-07')
        old = self.catalog.resolve(ROOT, None, number='AR-14')
        self.assertEqual((new['key'], new['type'], new['semantic_spec']), (NEW, 'flowchart', 'types/flowchart/1.0.0.md'))
        self.assertEqual((old['key'], old['type']), (OLD, 'architecture'))
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            self.assertEqual(self.catalog.resolve(ROOT, None, number='FC-07', line_style=line)['line_style'], line)

    def test_only_new_card_in_flowchart_without_original(self):
        page = (ROOT / 'assets/style-gallery.html').read_text(encoding='utf8')
        flow = page.split('<section id="type-flowchart"', 1)[1].split('</section>', 1)[0]
        arch = page.split('<section id="type-architecture"', 1)[1].split('</section>', 1)[0]
        self.assertIn('data-style-number="FC-07"', flow)
        card = flow.split('data-style-number="FC-07"', 1)[1].split('</article>', 1)[0]
        self.assertIn('data-style-number="AR-14"', arch)  # 静态 HTML 保留历史内容，载入后按替代标记移除
        self.assertIn('data-gallery-replaces="AR-14"', card)
        self.assertNotIn('查看原始样例图', card, '公开版本不随附参考原图')


if __name__ == '__main__':
    unittest.main()
