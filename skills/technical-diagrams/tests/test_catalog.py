import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CatalogTests(unittest.TestCase):
    def setUp(self):
        script = ROOT / 'scripts' / 'catalog.py'
        self.assertTrue(script.exists(), '缺少风格选择和兼容性校验工具')
        spec = importlib.util.spec_from_file_location('diagram_catalog', script)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_resolve_pins_explicit_style_version(self):
        result = self.module.resolve(ROOT, 'state', 'classic-mono', '1.0.0')
        self.assertEqual(result['key'], 'state/classic-mono@1.0.0')
        self.assertTrue(Path(result['spec_path']).is_file())

    def test_defaults_are_independent_for_each_type(self):
        expected = {'flowchart': 'soft-process', 'sequence': 'institutional-blue',
                    'state': 'classic-mono', 'architecture': 'soft-layered'}
        for kind, style in expected.items():
            self.assertEqual(self.module.resolve(ROOT, kind)['style'], style)

    def test_chinese_alias_requires_matching_type(self):
        self.assertEqual(self.module.resolve(ROOT, 'state', '经典黑白')['style'], 'classic-mono')

    def test_unknown_style_and_cross_type_profile_do_not_fallback(self):
        with self.assertRaises(ValueError):
            self.module.resolve(ROOT, 'sequence', 'state/classic-mono@1.0.0')
        with self.assertRaises(ValueError):
            self.module.resolve(ROOT, 'state', 'does-not-exist')

    def test_locked_package_is_valid(self):
        self.assertEqual(self.module.validate(ROOT), [])

    def clone(self):
        scratch = ROOT.parents[1] / '.data-cache' / 'technical-diagrams-tests'
        scratch.mkdir(parents=True, exist_ok=True)
        target = scratch / ('diagram-test-' + uuid.uuid4().hex)
        def cleanup():
            resolved = target.resolve()
            self.assertEqual(resolved.parent, scratch.resolve())
            self.assertTrue(resolved.name.startswith('diagram-test-'))
            shutil.rmtree(resolved)
        self.addCleanup(cleanup)
        shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', 'node_modules'))
        return target

    def read_type(self, root, kind):
        return json.loads((root / 'registry' / 'types' / f'{kind}.json').read_text(encoding='utf-8'))

    def write_type(self, root, kind, data):
        (root / 'registry' / 'types' / f'{kind}.json').write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def read_shared(self, root, name):
        return json.loads((root / 'registry' / 'shared' / name).read_text(encoding='utf-8'))

    def write_shared(self, root, name, data):
        (root / 'registry' / 'shared' / name).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    def test_new_style_does_not_change_old_resolution(self):
        root = self.clone()
        before = self.module.resolve(root, 'state')
        old_bytes = Path(before['spec_path']).read_bytes()
        typ = self.read_type(root, 'state')
        prefix = 'styles/state/isolated-example/1.0.0'
        source = root / 'styles/state/classic-mono/1.0.0'
        target = root / prefix
        shutil.copytree(source, target)
        tokens = json.loads((target / 'tokens.json').read_text(encoding='utf-8'))
        tokens['profile'] = 'state/isolated-example@1.0.0'
        (target / 'tokens.json').write_text(json.dumps(tokens), encoding='utf-8')
        typ['styles'].append({'id': 'isolated-example', 'version': '1.0.0', 'number': 'ST-99',
                              'name': '隔离扩展示例', 'aliases': []})
        typ['style_versions']['isolated-example'] = '1.0.0'
        self.write_type(root, 'state', typ)
        self.assertEqual(self.module.resolve(root, 'state')['key'], before['key'])
        self.assertEqual(Path(before['spec_path']).read_bytes(), old_bytes)
        self.assertEqual(self.module.validate(root), [])

    def test_resolve_returns_only_current_type_guide(self):
        result = self.module.resolve(ROOT, 'flowchart')
        self.assertEqual(result['type_guide_path'], str(ROOT / 'references/type-guides/flowchart.md'))
        self.assertFalse([key for key in result['dependency_hashes'] if key.startswith('references/type-guides/')])

    def test_new_type_needs_only_index_entry_and_type_file(self):
        root = self.clone()
        source = root / 'styles/state/classic-mono/1.0.0'
        target = root / 'styles/widgets/basic/1.0.0'
        shutil.copytree(source, target)
        tokens = json.loads((target / 'tokens.json').read_text(encoding='utf-8'))
        tokens['profile'] = 'widgets/basic@1.0.0'
        (target / 'tokens.json').write_text(json.dumps(tokens), encoding='utf-8')
        (root / 'types/widgets').mkdir(parents=True)
        (root / 'types/widgets/1.0.0.md').write_text('新增图种语义规范，测试类型隔离。', encoding='utf-8')
        (root / 'registry/types/widgets.json').write_text(json.dumps({
            'schema_version': 1, 'id': 'widgets', 'name': '部件图', 'aliases': ['部件关系图'],
            'semantic_version': '1.0.0', 'number_prefix': 'WG',
            'default': 'widgets/basic@1.0.0', 'style_versions': {'basic': '1.0.0'},
            'styles': [{'id': 'basic', 'version': '1.0.0', 'number': 'WG-01', 'name': '基础部件图', 'aliases': []}]
        }, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        index_path = root / 'registry/index.json'
        index = json.loads(index_path.read_text(encoding='utf-8'))
        index['types'].append('widgets')
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        self.assertEqual(self.module.validate(root), [])
        result = self.module.resolve(root, 'widgets')
        self.assertEqual(result['key'], 'widgets/basic@1.0.0')
        self.assertNotIn('type_guide_path', result)
        self.assertEqual((root / 'SKILL.md').read_text(encoding='utf-8'),
                         (ROOT / 'SKILL.md').read_text(encoding='utf-8'))

    def test_editing_frozen_style_or_default_is_rejected(self):
        root = self.clone()
        selected = self.module.resolve(root, 'state')
        with Path(selected['spec_path']).open('a', encoding='utf-8') as stream:
            stream.write('\n意外修改旧规范\n')
        self.assertTrue(any('冻结' in error for error in self.module.validate(root)))
        with self.assertRaises(ValueError):
            self.module.resolve(root, 'state')
        root = self.clone()
        typ = self.read_type(root, 'state')
        typ['default'] = 'state/soft-cards@1.0.0'
        self.write_type(root, 'state', typ)
        self.assertTrue(any('默认' in error for error in self.module.validate(root)))

    def test_paths_cannot_escape_skill_directory(self):
        root = self.clone()
        typ = self.read_type(root, 'flowchart')
        typ['guide'] = '../outside.md'
        self.write_type(root, 'flowchart', typ)
        self.assertTrue(any('越界' in error for error in self.module.validate(root)))

    def test_duplicate_profile_is_rejected(self):
        root = self.clone()
        typ = self.read_type(root, 'flowchart')
        typ['styles'].append(dict(typ['styles'][0]))
        self.write_type(root, 'flowchart', typ)
        self.assertTrue(any('重复' in error for error in self.module.validate(root)))

    def test_new_semantic_version_is_opt_in_and_old_load_list_is_stable(self):
        root = self.clone()
        old = self.module.resolve(root, 'state', 'classic-mono', '1.0.0')
        (root / 'types/state/2.0.0.md').write_text('新语义规范，测试显式版本隔离。', encoding='utf-8')
        source = root / 'styles/state/classic-mono/1.0.0'
        target = root / 'styles/state/classic-mono/2.0.0'
        shutil.copytree(source, target)
        tokens = json.loads((target / 'tokens.json').read_text(encoding='utf-8'))
        tokens['profile'] = 'state/classic-mono@2.0.0'
        (target / 'tokens.json').write_text(json.dumps(tokens), encoding='utf-8')
        typ = self.read_type(root, 'state')
        entry = dict(next(item for item in typ['styles'] if item['id'] == 'classic-mono'))
        entry.update(version='2.0.0', number='ST-03', semantic_version='2.0.0')
        typ['styles'].append(entry)
        self.write_type(root, 'state', typ)
        current = self.module.resolve(root, 'state', 'classic-mono')
        explicit = self.module.resolve(root, 'state', 'classic-mono', '2.0.0')
        self.assertEqual(current['type_spec_path'], old['type_spec_path'])
        self.assertEqual(current['tokens_path'], old['tokens_path'])
        self.assertTrue(explicit['type_spec_path'].endswith('2.0.0.md'))
        self.assertEqual(self.module.validate(root), [])

    def test_shared_root_instructions_are_frozen_too(self):
        root = self.clone()
        with (root / 'SKILL.md').open('a', encoding='utf-8') as stream:
            stream.write('\n意外注入新的全局默认颜色。\n')
        self.assertTrue(any('冻结' in error for error in self.module.validate(root)))

    def test_style_number_selects_one_fixed_profile(self):
        by_number = self.module.resolve(ROOT, None, number='st-01')
        by_style = self.module.resolve(ROOT, None, 'ST-01')
        self.assertEqual(by_number['key'], 'state/classic-mono@1.0.0')
        self.assertEqual(by_number['number'], 'ST-01')
        self.assertEqual(by_number, by_style)

    def test_number_rejects_unknown_type_and_version_conflicts(self):
        for kind, number, version in [(None, 'ST-99', None),
                                      ('sequence', 'ST-01', None),
                                      (None, 'ST-01', '2.0.0')]:
            with self.subTest(kind=kind, number=number, version=version):
                with self.assertRaises(ValueError):
                    self.module.resolve(ROOT, kind, version=version, number=number)

    def test_number_mapping_cannot_be_rebound(self):
        root = self.clone()
        typ = self.read_type(root, 'state')
        next(item for item in typ['styles'] if item['id'] == 'classic-mono')['number'] = 'ST-02'
        self.write_type(root, 'state', typ)
        self.assertTrue(any('编号' in error for error in self.module.validate(root)))
        with self.assertRaises(ValueError):
            self.module.resolve(root, None, number='ST-01')

    def test_gallery_groups_and_numbers_survive_profile_reordering(self):
        root = self.clone()
        index_path = root / 'registry' / 'index.json'
        index = json.loads(index_path.read_text(encoding='utf-8'))
        index['types'].reverse()
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        for kind in index['types']:
            typ = self.read_type(root, kind)
            typ['styles'].reverse()
            self.write_type(root, kind, typ)
        self.assertEqual(self.module.resolve(root, None, number='FC-01')['key'],
                         'flowchart/soft-process@1.0.0')
        target = root / 'assets' / 'test-gallery.html'
        self.module.gallery(root, target)
        page = target.read_text(encoding='utf-8')
        for kind in ('flowchart', 'sequence', 'state', 'architecture'):
            self.assertEqual(page.count(f'<section id="type-{kind}"'), 1)
        for code in ('FC-01', 'FC-02', 'SQ-01', 'SQ-02', 'ST-01', 'ST-02', 'AR-01', 'AR-02'):
            self.assertEqual(page.count(f'data-style-number="{code}"'), 1)
        self.assertLess(page.index('data-style-number="ST-01"'), page.index('data-style-number="ST-02"'))

    def test_er_type_has_independent_numbered_profiles(self):
        first = self.module.resolve(ROOT, None, number='ER-01')
        second = self.module.resolve(ROOT, '实体关系图', 'classic-mono')
        self.assertEqual(first['key'], 'er/soft-tables@1.0.0')
        self.assertEqual(second['number'], 'ER-02')
        self.assertEqual(self.module.resolve(ROOT, 'er')['key'], first['key'])
        self.assertIn('types/er/1.0.0.md', first['dependency_hashes'])
        self.assertNotIn('types/architecture/1.0.0.md', first['dependency_hashes'])

    def test_er_extension_keeps_all_existing_style_numbers(self):
        expected = {
            'FC-01':'flowchart/soft-process@1.0.0', 'FC-02':'flowchart/classic-mono@1.0.0',
            'SQ-01':'sequence/institutional-blue@1.0.0', 'SQ-02':'sequence/classic-mono@1.0.0',
            'ST-01':'state/classic-mono@1.0.0', 'ST-02':'state/soft-cards@1.0.0',
            'AR-01':'architecture/soft-layered@1.0.0', 'AR-02':'architecture/premium-cards@1.0.0'}
        for code, key in expected.items():
            self.assertEqual(self.module.resolve(ROOT, None, number=code)['key'], key)

    def test_line_style_defaults_to_orthogonal(self):
        result = self.module.resolve(ROOT, 'flowchart')
        self.assertEqual(result.get('line_style'), 'orthogonal')
        self.assertEqual(result.get('line_style_version'), '1.0.0')
        self.assertTrue(Path(result['line_spec_path']).is_file())
        self.assertIn('references/line-styles-v1.md', result['dependency_hashes'])

    def test_line_style_ids_names_and_aliases(self):
        options = {'orthogonal': ['orthogonal', '直角折线', '直角'],
                   'rounded-orthogonal': ['rounded-orthogonal', '圆角折线', '圆角'],
                   'curved': ['curved', '直连曲线', '曲线']}
        for expected, names in options.items():
            for name in names:
                with self.subTest(name=name):
                    result = self.module.resolve(ROOT, 'flowchart', line_style=name)
                    self.assertEqual(result['line_style'], expected)

    def test_line_style_survives_all_style_selection_paths(self):
        selectors = [dict(kind='flowchart'), dict(kind=None, number='FC-01'),
                     dict(kind=None, style='FC-01'),
                     dict(kind=None, style='flowchart/soft-process@1.0.0'),
                     dict(kind='流程图', style='浅色业务流程')]
        for selector in selectors:
            with self.subTest(selector=selector):
                result = self.module.resolve(ROOT, **selector, line_style='圆角折线')
                self.assertEqual(result['key'], 'flowchart/soft-process@1.0.0')
                self.assertEqual(result['number'], 'FC-01')
                self.assertEqual(result['line_style'], 'rounded-orthogonal')

    def test_full_profile_names_resolve_without_changing_registration(self):
        data = self.module.read_catalog(ROOT)
        for item in data['profiles']:
            with self.subTest(name=item['name']):
                result = self.module.resolve(ROOT, item['type'], item['name'])
                self.assertEqual(result['key'], self.module.profile_key(item))

    def test_unknown_line_style_does_not_fallback(self):
        for value in ('unknown', '', '   '):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    self.module.resolve(ROOT, 'flowchart', line_style=value)

    def test_profile_name_alias_collision_is_rejected(self):
        root = self.clone()
        typ = self.read_type(root, 'flowchart')
        typ['styles'][0]['name'] = typ['styles'][1]['id']
        self.write_type(root, 'flowchart', typ)
        self.assertTrue(any('歧义' in error for error in self.module.validate(root)))

    def test_line_style_registry_and_spec_are_frozen(self):
        for mutation in ('default', 'version', 'name', 'aliases', 'spec', 'delete'):
            with self.subTest(mutation=mutation):
                root = self.clone()
                lines = self.read_shared(root, 'line-styles.json')
                if mutation == 'spec':
                    with (root / 'references/line-styles-v1.md').open('a', encoding='utf-8') as stream:
                        stream.write('\n修改已冻结的线条规则。\n')
                elif mutation == 'delete':
                    (root / 'registry/shared/line-styles.json').unlink()
                elif mutation in ('default', 'version'):
                    lines[mutation] = 'curved' if mutation == 'default' else '2.0.0'
                else:
                    lines['options']['orthogonal'][mutation] = '被修改' if mutation == 'name' else ['不同别名']
                if mutation != 'delete':
                    self.write_shared(root, 'line-styles.json', lines)
                self.assertTrue(self.module.validate(root))
                with self.assertRaises(ValueError):
                    self.module.resolve(root, 'flowchart')

    def test_new_line_option_can_append_without_changing_old_choices(self):
        root = self.clone()
        lines = self.read_shared(root, 'line-styles.json')
        lines['options']['new-route'] = {'name': '新路线', 'aliases': []}
        self.write_shared(root, 'line-styles.json', lines)
        self.assertEqual(self.module.validate(root), [])
        self.module.make_lock(root, append=True)
        self.assertEqual(self.module.resolve(root, 'flowchart')['line_style'], 'orthogonal')
        self.assertEqual(self.module.resolve(root, 'flowchart', line_style='新路线')['line_style'], 'new-route')

    def test_line_style_alias_collision_is_rejected(self):
        root = self.clone()
        lines = self.read_shared(root, 'line-styles.json')
        lines['options']['curved']['aliases'].append('直角折线')
        self.write_shared(root, 'line-styles.json', lines)
        self.assertTrue(any('歧义' in error for error in self.module.validate(root)))
        with self.assertRaises(ValueError):
            self.module.resolve(root, 'flowchart', line_style='直角折线')

    def test_malformed_line_option_is_reported_as_registration_error(self):
        for value in (None, 'invalid', [], 1):
            with self.subTest(value=value):
                root = self.clone()
                lines = self.read_shared(root, 'line-styles.json')
                lines['options']['curved'] = value
                self.write_shared(root, 'line-styles.json', lines)
                self.assertTrue(self.module.validate(root))
                with self.assertRaises(ValueError):
                    self.module.resolve(root, 'flowchart')

    def test_line_style_cli_listing_and_combination(self):
        script = str(ROOT / 'scripts/catalog.py')
        listed = subprocess.run([sys.executable, '-B', script, 'list', '--line-styles'],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(listed.returncode, 0, listed.stderr)
        options = json.loads(listed.stdout)
        self.assertEqual([item['id'] for item in options], ['orthogonal', 'rounded-orthogonal', 'curved'])
        self.assertEqual([item['id'] for item in options if item['default']], ['orthogonal'])
        selected = subprocess.run([sys.executable, '-B', script, 'resolve', '--number', 'FC-01',
                                   '--line-style', '圆角折线'], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(selected.returncode, 0, selected.stdout + selected.stderr)
        self.assertEqual(json.loads(selected.stdout)['line_style'], 'rounded-orthogonal')
        rejected = subprocess.run([sys.executable, '-B', script, 'resolve', '--number', 'FC-01',
                                   '--line-style', 'wrong'], capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(rejected.returncode, 2)
        self.assertIn('线条', json.loads(rejected.stdout)['error'])

    def test_gallery_lists_line_choices_and_selected_previews(self):
        root = self.clone()
        target = root / 'assets/test-gallery.html'
        self.module.gallery(root, target)
        page = target.read_text(encoding='utf-8')
        for id in ('orthogonal', 'rounded-orthogonal', 'curved'):
            self.assertEqual(page.count(f'data-line-style="{id}"'), 1)
        preview_index = json.loads((root / 'assets/gallery-examples/index.json').read_text(encoding='utf-8'))
        for item in self.module.read_catalog(root)['profiles']:
            key = self.module.profile_key(item)
            path = preview_index.get(key, item['example'])
            self.assertIn((root / path).read_text(encoding='utf-8'), page)
            self.assertTrue((root / item['example']).is_file())
        self.assertIn('线条样式', page)
        self.assertIn('圆角折线', page)

    def test_interaction_standard_is_loaded_for_all_visual_and_line_choices(self):
        data = self.module.read_catalog(ROOT)
        for code, key in data['style_numbers'].items():
            for line in data['line_styles']['options']:
                with self.subTest(code=code, line=line):
                    result = self.module.resolve(ROOT, None, number=code, line_style=line)
                    self.assertEqual(result['key'], key)
                    self.assertEqual(result['line_style'], line)
                    self.assertEqual(result['interaction_standard'], 'single-direction')
                    self.assertEqual(result['interaction_standard_version'], '1.0.0')
                    self.assertTrue(Path(result['interaction_spec_path']).is_file())
                    self.assertTrue(Path(result['interaction_example_path']).is_file())
                    self.assertIn('references/interaction-standards/1.0.0.md', result['dependency_hashes'])
                    self.assertIn('references/interaction-standards/1.0.0.svg', result['dependency_hashes'])

    def test_interaction_standard_registration_and_dependencies_are_frozen(self):
        for mutation in ('delete', 'version', 'example', 'content'):
            with self.subTest(mutation=mutation):
                root = self.clone()
                standard = self.read_shared(root, 'interaction.json')
                if mutation == 'delete':
                    (root / 'registry/shared/interaction.json').unlink()
                elif mutation == 'version':
                    standard['version'] = '2.0.0'
                elif mutation == 'example':
                    standard['example'] = 'styles/state/classic-mono/1.0.0/example.svg'
                else:
                    with (root / standard['spec']).open('a', encoding='utf-8') as stream:
                        stream.write('\n意外改变交互规范。\n')
                if mutation != 'delete':
                    self.write_shared(root, 'interaction.json', standard)
                self.assertTrue(self.module.validate(root))
                with self.assertRaises(ValueError):
                    self.module.resolve(root, None, number='AR-01')

    def test_gallery_includes_one_shared_interaction_example(self):
        root = self.clone()
        destination = root / 'assets' / 'test-gallery.html'
        self.module.gallery(root, destination)
        page = destination.read_text(encoding='utf-8')
        self.assertEqual(page.count('id="interaction-standards"'), 1)
        self.assertIn('单向交互', page)
        self.assertIn('虚线返回', page)
        self.assertIn((root / 'references/interaction-standards/1.0.0.svg').read_text(encoding='utf-8'), page)

    def test_synthetic_layered_template_is_append_only_and_selectable(self):
        result = self.module.resolve(ROOT, None, number='AR-03')
        self.assertEqual(result['key'], 'architecture/layered-interactions@1.0.0')
        self.assertEqual(self.module.resolve(ROOT, 'architecture')['number'], 'AR-01')
        for line in ('orthogonal', 'rounded-orthogonal', 'curved'):
            chosen = self.module.resolve(ROOT, None, number='AR-03', line_style=line)
            self.assertEqual(chosen['line_style'], line)

    def test_synthetic_template_has_no_embedded_or_external_source_payload(self):
        import xml.etree.ElementTree as ET
        selected = self.module.resolve(ROOT, None, number='AR-03')
        payload = Path(selected['example_path']).read_text(encoding='utf-8')
        svg = ET.fromstring(payload)
        self.assertNotIn('<!--', payload)
        self.assertFalse(any(el.tag.rsplit('}', 1)[-1] in ('image', 'script', 'foreignObject') for el in svg.iter()))
        self.assertFalse(any('href' in key for el in svg.iter() for key in el.attrib))
        metadata = next(el for el in svg.iter() if el.tag.endswith('metadata'))
        model = json.loads(metadata.text)
        self.assertEqual(model['sample_kind'], 'synthetic')
        self.assertEqual(set(model), {'profile', 'number', 'sample_kind', 'line_style', 'interaction_standard', 'model'})
        self.assertTrue(all(value.startswith('tpl-layered-v1-') for el in svg.iter() for key,value in el.attrib.items() if key=='id'))


if __name__ == '__main__':
    unittest.main()
