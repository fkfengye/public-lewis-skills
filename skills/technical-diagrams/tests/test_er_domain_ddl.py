"""ER-03 多域 DDL 表结构：资源与注册一致性测试。

独立于 catalog.lock.json 冻结基线，直接核对注册表、风格资源与展示样例。
"""
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = 'er/domain-ddl@1.0.0'
STYLE_DIR = ROOT / 'styles/er/domain-ddl/1.0.0'


def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def tag(element):
    return element.tag.rsplit('}', 1)[-1]


class ER03DomainDDLTests(unittest.TestCase):

    def test_registry_entry_and_unique_number(self):
        data = read_json('registry/types/er.json')
        entry = next((s for s in data['styles'] if s['id'] == 'domain-ddl'), None)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['version'], '1.0.0')
        self.assertEqual(entry['number'], 'ER-03')
        self.assertEqual(data['style_versions']['domain-ddl'], '1.0.0')
        self.assertEqual(data['default'], 'er/soft-tables@1.0.0')
        numbers = [s['number'] for s in data['styles']]
        self.assertEqual(len(numbers), len(set(numbers)))

    def test_tokens_profile_and_new_palette(self):
        tokens = read_json('styles/er/domain-ddl/1.0.0/tokens.json')
        self.assertEqual(tokens['profile'], KEY)
        self.assertEqual(tokens['schema_version'], 1)
        palette = tokens['palette']
        for field, value in (('band', '#F7FAFC'), ('badge', '#2F6FA8'), ('key', '#A2531C')):
            self.assertEqual(palette[field], value)
        self.assertEqual(tokens['table']['row_height'], 44)
        self.assertEqual(tokens['geometry']['connector_radius'], 16)
        self.assertFalse(tokens['geometry']['shadow'])

    def test_spec_and_analysis_exist(self):
        spec = (STYLE_DIR / 'SPEC.md').read_text(encoding='utf-8')
        analysis = (STYLE_DIR / 'reference-analysis.md').read_text(encoding='utf-8')
        for phrase in ('四段式', '键 / 字段 / 类型·可空', '圆角正交折线', '不表示基数'):
            self.assertIn(phrase, spec)
        for phrase in ('原图观察', '可复用视觉规则', '待确认'):
            self.assertIn(phrase, analysis)

    def test_example_svg_metadata_and_model(self):
        root = ET.parse(STYLE_DIR / 'example.svg').getroot()
        self.assertEqual(tag(root), 'svg')
        metadata = next((e for e in root.iter() if tag(e) == 'metadata'), None)
        self.assertIsNotNone(metadata)
        data = json.loads(metadata.text)
        self.assertEqual(data['profile'], KEY)
        self.assertEqual(data['number'], 'ER-03')
        self.assertEqual(data['sample_kind'], 'synthetic')
        self.assertEqual(data['semantic_version'], '1.0.0')
        self.assertEqual(data['line_style']['id'], 'rounded-orthogonal')
        self.assertEqual(data['interaction_standard']['id'], 'single-direction')
        self.assertGreaterEqual(len(data['dependencies']), 10)
        self.assertNotIn('styles/er/domain-ddl/1.0.0/example.svg', data['dependencies'])
        model = data['model']
        self.assertEqual(len(model['domains']), 3)
        self.assertEqual(len(model['entities']), 9)
        self.assertEqual(len(model['relationships']), 8)
        for rel in model['relationships']:
            self.assertEqual(rel['kind'], 'physical_fk')
            self.assertEqual(len(rel['from']['fields']), 1)
            self.assertEqual(len(rel['to']['fields']), 1)

    def test_example_covers_feature_checklist(self):
        root = ET.parse(STYLE_DIR / 'example.svg').getroot()
        counts = {}
        for element in root.iter():
            counts[tag(element)] = counts.get(tag(element), 0) + 1
        self.assertEqual(counts.get('polygon'), 8)          # 8 个引用箭头
        connectors = [e for e in root.iter()
                      if tag(e) == 'path' and e.get('data-diagram-role') == 'connector']
        self.assertEqual(len(connectors), 8)
        self.assertTrue(all('Q' in e.get('d', '') for e in connectors))
        dashed = [e for e in root.iter() if e.get('stroke-dasharray') == '10 7']
        self.assertEqual(len(dashed), 3)                   # 三个业务域虚线框
        texts = ''.join(''.join(e.itertext()) for e in root.iter() if tag(e) == 'text')
        for phrase in ('键与可空速查', '约束与实现边界', '角色外键索引',
                       'FK/UK', 'UK*', '基数待确认', '范围：'):
            self.assertIn(phrase, texts)
        for forbidden in ('工单', 'ticket_', '企业工单系统'):
            self.assertNotIn(forbidden, texts)             # 通用示例不复用原图业务数据

    def test_original_reference_is_not_shipped(self):
        index = read_json('assets/reference-examples/index.json')
        self.assertEqual(index, {}, '公开版本不随附参考原图')
        self.assertFalse((ROOT / 'assets/reference-examples/er-03-original.svg').exists())

    def test_edge_labels_carry_cardinality_ratios(self):
        root = ET.parse(STYLE_DIR / 'example.svg').getroot()
        metadata = next((e for e in root.iter() if tag(e) == 'metadata'), None)
        data = json.loads(metadata.text)
        ratios = [rel.get('cardinality_ratio') for rel in data['model']['relationships']]
        self.assertEqual(len(ratios), 8)
        self.assertTrue(all(r and ':' in r for r in ratios))
        self.assertIn('0..1:0..*', ratios)
        self.assertEqual(ratios.count('1:1'), 1)
        texts = ''.join(''.join(e.itertext()) for e in root.iter() if tag(e) == 'text')
        self.assertIn('跨线不连接', texts)
        self.assertIn('引用端可见目标数', texts)
        self.assertIn('基数待确认', texts)

    def test_quantified_routing_and_bridge_coverage(self):
        root = ET.parse(STYLE_DIR / 'example.svg').getroot()
        connectors = [e for e in root.iter()
                      if tag(e) == 'path' and e.get('data-diagram-role') == 'connector']
        self.assertEqual(len(connectors), 8)
        self.assertTrue(all('Q' in e.get('d', '') for e in connectors))
        bridges = sum(e.get('d', '').count(' A') for e in connectors)
        metadata = next((e for e in root.iter() if tag(e) == 'metadata'), None)
        data = json.loads(metadata.text)
        routing = data['overrides']['connectors']['routing']
        self.assertEqual(routing['order'], 'bend -> length -> crossing')
        self.assertEqual(routing['bends_per_connector'], 2)
        self.assertEqual(routing['crossing_bridges'], bridges)
        self.assertGreater(bridges, 0)
        self.assertEqual(data['overrides']['connectors']['bridge_radius_max'], 12)

    def test_layout_separates_ports_and_reduces_routing(self):
        """按引用链重排行序后：近直连增多、交叉减少、同字段箭头分侧且不越行。"""
        svg_text = (STYLE_DIR / 'example.svg').read_text(encoding='utf-8')
        root = ET.fromstring(svg_text)
        metadata = next((e for e in root.iter() if tag(e) == 'metadata'), None)
        routing = json.loads(metadata.text)['overrides']['connectors']['routing']
        self.assertEqual(routing['direct_connectors'], 4)
        self.assertEqual(routing['channel_connectors'], 4)
        self.assertEqual(routing['crossing_bridges'], 3)
        self.assertIn('±14', routing['port_separation'])
        self.assertIn('不依赖白色遮罩', routing['label_placement'])
        # 标签靠几何避让，不用白色遮罩压线
        self.assertNotIn('paint-order', svg_text)

        texts = [''.join(e.itertext()) for e in root.iter() if tag(e) == 'text']
        for label in ('开设课程 1:0..*', '选课学员 1:0..*',
                      '结业归属 1:1', '课时资源 1:0..*'):
            self.assertIn(label, texts)

        arrows = []
        for e in root.iter():
            if tag(e) != 'polygon':
                continue
            pts = e.get('points').split()
            x, y = pts[0].split(',')
            arrows.append((float(x), float(y)))
        self.assertEqual(len(arrows), 8)
        self.assertGreaterEqual(len({x for x, _ in arrows}), 3)  # 入线侧不再只有右边缘
        # cohort.id 行范围 1368~1412：3 条引用拆成左 2 右 1，同侧间距 28
        cohort = [(x, y) for x, y in arrows
                  if 1368 <= y <= 1412 and x in (1020.0, 1720.0)]  # 排除同层 course.id 的箭头
        self.assertEqual(len(cohort), 3)
        left = sorted(y for x, y in cohort if x == 1020)
        right = [y for x, y in cohort if x == 1720]
        self.assertEqual(len(left), 2)
        self.assertEqual(len(right), 1)
        self.assertGreaterEqual(left[1] - left[0], 28)
        self.assertTrue(all(1368 <= y <= 1412 for y in left + right))
        # 布局与端口规则已进入 SPEC
        spec = (STYLE_DIR / 'SPEC.md').read_text(encoding='utf-8')
        for phrase in ('域内行序优先按引用链重排', '入线侧按来源域决定',
                       '端口不越行', '标签避让实线'):
            self.assertIn(phrase, spec)

    def test_quantified_rules_are_in_frozen_specs(self):
        line_spec = (ROOT / 'references/line-styles-v1.md').read_text(encoding='utf-8')
        for phrase in ('弯折数', '路径长度', '交叉数', '最小弯折数',
                       '最短路径', '最少交叉数', '剩余交叉一律圆弧桥处理', '基数比例'):
            self.assertIn(phrase, line_spec)
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('最小弯折数 → 最短路径 → 最少交叉数', skill)
        self.assertIn('基数比例', skill)
        self.assertIn('基数比例', (ROOT / 'types/er/1.0.0.md').read_text(encoding='utf-8'))
        self.assertIn('基数比例', (STYLE_DIR / 'SPEC.md').read_text(encoding='utf-8'))

    def test_documentation_entries(self):
        guide = (ROOT / 'references/type-guides/er.md').read_text(encoding='utf-8')
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        numbering = (ROOT / 'references/style-numbering-v1.md').read_text(encoding='utf-8')
        changelog = (ROOT / 'references/changelog.md').read_text(encoding='utf-8')
        self.assertIn('ER-03', guide)
        self.assertIn('reference-analysis.md', guide)
        er_section = readme.split('### ER 图\n', 1)[1].split('\n### ', 1)[0]
        self.assertIn('| ER-03 | 多域 DDL 表结构 | |', er_section)
        self.assertIn('| ER 图 `er` | 逻辑模型、物理表结构、字段级关系 | 3 |', readme)
        self.assertIn('按引用链重排域内表卡行序', readme)
        self.assertIn('分到表卡左右两侧端口', readme)
        self.assertIn('### 量化布线指标', readme)
        self.assertIn('减少交叉不得以增加弯折或路径长度为代价', readme)
        self.assertIn('er/domain-ddl@1.0.0', numbering)
        self.assertIn('ER-03 多域 DDL 表结构入口', changelog)


if __name__ == '__main__':
    unittest.main()
