#!/usr/bin/env python3
"""图种/风格路由与追加兼容性校验；注册表按图种拆分，只依赖 Python 标准库。"""
import argparse
import base64
import hashlib
import html
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r'^[a-z][a-z0-9-]*$')
VERSION = re.compile(r'^\d+\.\d+\.\d+$')
STYLE_NUMBER = re.compile(r'^[A-Z][A-Z0-9]{1,5}-\d{2,}$')
PROFILE_KEY = re.compile(r'([^/]+)/([^@]+)@(\d+\.\d+\.\d+)')
REGISTRY = 'registry/index.json'

CORE_FILES = ['SKILL.md', 'scripts/catalog.py', 'scripts/render_svg.mjs', 'agents/openai.yaml',
              'references/extensions-v1.md', 'references/html-integration-v1.md',
              'references/style-numbering-v1.md']


def read_json(path, label='注册文件'):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise ValueError(f'缺少{label}：{Path(path).name}') from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f'{label}不是有效 JSON：{Path(path).name}：{exc}') from exc


def read_index(root):
    return read_json(Path(root) / REGISTRY, '注册表索引')


def local_file(root, relative):
    root = Path(root).resolve()
    rel = Path(relative)
    if not isinstance(relative, str) or rel.is_absolute() or '..' in rel.parts or '\\' in relative or ':' in relative:
        raise ValueError(f'资源路径越界或非可移植相对路径：{relative}')
    candidate = (root / rel).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f'资源路径越界：{relative}')
    if not candidate.is_file():
        raise ValueError(f'资源文件不存在：{relative}')
    return candidate


def profile_key(item):
    return f"{item['type']}/{item['id']}@{item['version']}"


def normalize_type(data, kind):
    kind = kind.strip().casefold() if isinstance(kind, str) else kind
    if kind in data['types']:
        return kind
    matches = [key for key, value in data['types'].items() if kind in [a.strip().casefold() for a in value.get('aliases', [])]]
    if len(matches) != 1:
        raise ValueError(f'未知或歧义图种：{kind}；可选 {list(data["types"])}')
    return matches[0]


def style_number(data, key):
    matches = [code for code, value in data.get('style_numbers', {}).items() if value == key]
    if len(matches) > 1:
        raise ValueError(f'同一风格版本存在多个编号：{key}')
    return matches[0] if matches else None


def line_style_errors(root, data, lock=None):
    errors = []
    try:
        lines = data.get('line_styles')
        if not isinstance(lines, dict):
            raise ValueError('缺少线条样式注册 line_styles')
        if not VERSION.fullmatch(lines.get('version', '')):
            raise ValueError('非法线条规范版本')
        local_file(root, lines['spec'])
        options = lines['options']
        if not isinstance(options, dict) or not options:
            raise ValueError('线条样式选项不能为空')
        if lines['default'] not in options:
            errors.append('默认线条样式未注册')
        names = {}
        for ident, item in options.items():
            if not isinstance(item, dict):
                raise ValueError(f'线条样式条目必须为对象：{ident}')
            if not ID.fullmatch(ident) or not isinstance(item.get('name'), str) or not item['name'].strip():
                raise ValueError(f'非法线条样式注册：{ident}')
            if not isinstance(item.get('aliases', []), list):
                raise ValueError(f'线条别名必须为数组：{ident}')
            for name in [ident, item['name']] + item.get('aliases', []):
                if not isinstance(name, str) or not name.strip():
                    raise ValueError(f'非法线条别名：{ident}')
                normalized = name.strip().casefold()
                if normalized in names and names[normalized] != ident:
                    errors.append(f'线条样式名称或别名歧义：{name}')
                names[normalized] = ident
        frozen = (lock or {}).get('line_styles', {})
        for field in ('default', 'version', 'spec'):
            if field in frozen and lines.get(field) != frozen[field]:
                errors.append(f'冻结线条注册被修改：{field}')
        for ident, item in frozen.get('options', {}).items():
            if options.get(ident) != item:
                errors.append(f'冻结线条样式被修改或删除：{ident}')
    except (KeyError, TypeError, ValueError, OSError) as exc:
        errors.append(str(exc))
    return errors


def interaction_standard_errors(root, data, lock=None):
    errors = []
    try:
        standard = data.get('interaction_standard')
        if not isinstance(standard, dict):
            raise ValueError('缺少交互规范注册 interaction_standard')
        if not ID.fullmatch(standard.get('id', '')) or not VERSION.fullmatch(standard.get('version', '')):
            raise ValueError('非法交互规范 ID 或版本')
        for field, suffix in (('spec', 'md'), ('example', 'svg')):
            expected = f"references/interaction-standards/{standard['version']}.{suffix}"
            if standard.get(field) != expected:
                raise ValueError(f'交互规范版本与资源路径不匹配：{field}')
            local_file(root, standard[field])
        frozen = (lock or {}).get('interaction_standard')
        if frozen is not None and standard != frozen:
            errors.append('冻结交互规范注册已改变；升级须经限定入口迁移')
    except (KeyError, TypeError, ValueError, OSError) as exc:
        errors.append(str(exc))
    return errors


def normalize_line_style(data, value):
    lines = data['line_styles']
    value = lines['default'] if value is None else value
    normalized = value.strip().casefold() if isinstance(value, str) else None
    matches = [ident for ident, item in lines['options'].items()
               if normalized in [name.strip().casefold() for name in [ident, item['name']] + item.get('aliases', [])]]
    if len(matches) != 1:
        options = [item['name'] for item in lines['options'].values()]
        raise ValueError(f'未知或歧义线条样式：{value}；可选 {options}')
    return matches[0]


def _text_list(value):
    return isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value)


def _compose_type(root, index, kind, issues, profiles, numbers):
    """加载单个图种定义文件并展开该图种的全部风格。"""
    path = Path(root) / 'registry' / 'types' / f'{kind}.json'
    try:
        spec = read_json(path, f'图种定义 {kind}')
    except ValueError as exc:
        issues.append(str(exc))
        return None
    if not ID.fullmatch(kind) or spec.get('id') != kind:
        issues.append(f'图种 ID 与文件名不一致：{kind}')
    if spec.get('schema_version') != 1:
        issues.append(f'图种定义 schema_version 必须为 1：{kind}')
    name = spec.get('name')
    if not isinstance(name, str) or not name.strip():
        issues.append(f'图种缺少名称：{kind}')
    type_aliases = spec.get('aliases', [])
    if not _text_list(type_aliases):
        issues.append(f'图种别名必须为非空字符串数组：{kind}')
        type_aliases = []
    semantic = spec.get('semantic_version')
    if not isinstance(semantic, str) or not VERSION.fullmatch(semantic):
        issues.append(f'图种语义版本非法：{kind}')
        semantic = '1.0.0'
    type_spec = f"types/{kind}/{semantic}.md"
    try:
        local_file(root, type_spec)
    except ValueError as exc:
        issues.append(str(exc))
    guide = spec.get('guide')
    if guide is not None:
        try:
            local_file(root, guide)
        except (ValueError, TypeError) as exc:
            issues.append(str(exc))
    default = spec.get('default')
    match = PROFILE_KEY.fullmatch(default) if isinstance(default, str) else None
    if not match or match.group(1) != kind:
        issues.append(f'图种默认风格必须是本图种完整 key：{kind}')
    pins = spec.get('style_versions')
    if not isinstance(pins, dict) or not pins:
        issues.append(f'图种缺少固定版本映射：{kind}')
        pins = {}
    for style, version in pins.items():
        if not ID.fullmatch(style) or not isinstance(version, str) or not VERSION.fullmatch(version):
            issues.append(f'非法固定版本：{kind}/{style}@{version}')
    styles = spec.get('styles')
    if not isinstance(styles, list) or not styles:
        issues.append(f'图种未注册任何风格：{kind}')
        styles = []
    type_def = {'name': name, 'aliases': type_aliases, 'spec': type_spec,
                'default': default, 'style_versions': pins}
    if guide is not None:
        type_def['guide'] = guide
    if 'gallery_layout' in spec:
        type_def['gallery_layout'] = spec['gallery_layout']
    common = index['common']
    seen_styles, local_aliases, seen_keys = {}, {}, set()
    for entry in styles:
        if not isinstance(entry, dict):
            issues.append(f'风格条目必须为对象：{kind}')
            continue
        sid, version = entry.get('id'), entry.get('version')
        if not isinstance(sid, str) or not ID.fullmatch(sid):
            issues.append(f'非法风格 ID：{kind}/{sid}')
            continue
        if not isinstance(version, str) or not VERSION.fullmatch(version):
            issues.append(f'非法风格版本：{kind}/{sid}')
            continue
        key = f'{kind}/{sid}@{version}'
        if key in seen_keys:
            issues.append(f'重复风格编号：{key}')
            continue
        seen_keys.add(key)
        if sid not in pins:
            issues.append(f'新增风格未声明固定版本：{key}')
        style_name = entry.get('name')
        if not isinstance(style_name, str) or not style_name.strip():
            issues.append(f'风格缺少名称：{key}')
        style_aliases = entry.get('aliases', [])
        if not _text_list(style_aliases):
            issues.append(f'风格别名必须为非空字符串数组：{key}')
            style_aliases = []
        semantic_version = entry.get('semantic_version', semantic)
        common_version = entry.get('common_version', common['version'])
        if not isinstance(semantic_version, str) or not VERSION.fullmatch(semantic_version):
            issues.append(f'非法语义版本：{key}')
            semantic_version = semantic
        if not isinstance(common_version, str) or not VERSION.fullmatch(common_version):
            issues.append(f'非法公共版本：{key}')
            common_version = common['version']
        base = f'styles/{kind}/{sid}/{version}'
        for field, filename in (('spec', 'SPEC.md'), ('tokens', 'tokens.json'), ('example', 'example.svg')):
            relative = f'{base}/{filename}'
            try:
                local_file(root, relative)
            except ValueError as exc:
                issues.append(str(exc))
            if field == 'spec':
                spec_path = relative
            elif field == 'tokens':
                tokens_path = relative
            else:
                example_path = relative
        try:
            token_data = read_json(root / tokens_path, 'tokens')
            if token_data.get('profile') != key or token_data.get('schema_version') != 1:
                issues.append(f'tokens 归属或 schema 不匹配：{key}')
        except ValueError as exc:
            issues.append(str(exc))
        for alias in [sid, style_name if isinstance(style_name, str) else ''] + style_aliases:
            normalized = alias.strip().casefold() if isinstance(alias, str) else ''
            if not normalized:
                continue
            if normalized in local_aliases and local_aliases[normalized] != sid:
                issues.append(f'风格别名歧义：{kind}/{alias}')
            local_aliases[normalized] = sid
        number = entry.get('number')
        if number is not None and (not isinstance(number, str) or not STYLE_NUMBER.fullmatch(number)):
            issues.append(f'非法风格编号：{key} {number}')
        profile = {'type': kind, 'id': sid, 'version': version, 'name': style_name,
                   'aliases': style_aliases,
                   'common_version': common_version,
                   'common_spec': f'references/common/{common_version}.md',
                   'semantic_version': semantic_version,
                   'semantic_spec': f'types/{kind}/{semantic_version}.md',
                   'spec': spec_path, 'tokens': tokens_path, 'example': example_path}
        for field in ('layout', 'gallery_layout'):
            if field in entry:
                if not isinstance(entry[field], str):
                    issues.append(f'{field} 必须为字符串：{key}')
                else:
                    profile[field] = entry[field]
        profiles.append(profile)
        if number is not None:
            if number in numbers:
                issues.append(f'风格编号重复：{number}')
            numbers[number] = key
        seen_styles.setdefault(sid, set()).add(version)
    for sid, version in pins.items():
        if version not in seen_styles.get(sid, set()):
            issues.append(f'固定版本指向未注册风格：{kind}/{sid}@{version}')
    return type_def


def compose_catalog(root, index, issues):
    """按索引加载注册表；返回与旧版聚合结构兼容的字典。"""
    root = Path(root)
    common = index.get('common')
    if not isinstance(common, dict) or not isinstance(common.get('version'), str) \
            or not VERSION.fullmatch(common['version']) or not isinstance(common.get('spec'), str):
        issues.append('注册表索引缺少合法 common 注册')
        common = {'version': '1.0.0', 'spec': 'references/common/1.0.0.md'}
    index = {**index, 'common': common}
    try:
        local_file(root, common['spec'])
    except ValueError as exc:
        issues.append(str(exc))
    shared = {}
    for field in ('line_styles', 'interaction_standard'):
        relative = index.get(field)
        if not isinstance(relative, str):
            issues.append(f'注册表索引缺少 {field}')
            continue
        try:
            local_file(root, relative)
            shared[field] = read_json(root / relative, field)
        except ValueError as exc:
            issues.append(str(exc))
    if index.get('schema_version') != 1:
        issues.append('不支持的 registry schema_version')
    kinds = index.get('types')
    if not isinstance(kinds, list) or not kinds or not all(isinstance(k, str) for k in kinds):
        issues.append('注册表索引 types 必须为非空字符串数组')
        kinds = []
    if len(set(kinds)) != len(kinds):
        issues.append('注册表索引 types 存在重复项')
    types, profiles, numbers = {}, [], {}
    type_aliases = {}
    for kind in kinds:
        if not ID.fullmatch(kind):
            issues.append(f'非法图种 ID：{kind}')
            continue
        item = _compose_type(root, index, kind, issues, profiles, numbers)
        if item is None:
            continue
        if kind in types:
            issues.append(f'重复图种：{kind}')
            continue
        types[kind] = item
        for alias in [kind] + item.get('aliases', []):
            normalized = alias.strip().casefold()
            if normalized in type_aliases and type_aliases[normalized] != kind:
                issues.append(f'图种别名歧义：{alias}')
            type_aliases[normalized] = kind
    return {'schema_version': 1,
            'skill_version': index.get('skill_version', ''),
            'common': common['spec'],
            'line_styles': shared.get('line_styles', {}),
            'types': types,
            'profiles': profiles,
            'style_numbers': numbers,
            'interaction_standard': shared.get('interaction_standard', {})}


def read_catalog(root):
    issues = []
    try:
        index = read_index(root)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    data = compose_catalog(root, index, issues)
    if issues:
        raise ValueError('\n'.join(issues))
    return data


def resolve(root, kind, style=None, version=None, number=None, line_style=None):
    data = read_catalog(root)
    if number is not None and style is not None:
        raise ValueError('编号和 style 二选一，避免选择歧义')
    if number is None and style and STYLE_NUMBER.fullmatch(style.strip().upper()):
        number, style = style, None
    if number is not None:
        code = number.strip().upper()
        key = data.get('style_numbers', {}).get(code)
        if key is None:
            raise ValueError(f'未知风格编号：{code}；请使用 list 查看可选编号')
        lock = read_json(Path(root) / 'catalog.lock.json', '冻结基线')
        if code in lock.get('style_numbers', {}) and lock['style_numbers'][code] != key:
            raise ValueError(f'冻结编号绑定已改变：{code}')
        result = resolve(root, kind, key, version, line_style=line_style)
        if result['number'] != code:
            raise ValueError(f'风格编号不是唯一映射：{code}')
        return result
    if style and '/' in style:
        match = PROFILE_KEY.fullmatch(style)
        if not match:
            raise ValueError('完整风格编号格式应为 type/style@1.0.0')
        selected_type, style, specified_version = match.groups()
        if kind is not None and normalize_type(data, kind) != selected_type:
            raise ValueError('完整风格编号与图种不匹配，禁止跨图种回退')
        if version and version != specified_version:
            raise ValueError('两个版本参数不一致')
        kind, version = selected_type, specified_version
    if kind is None:
        raise ValueError('请提供图种，或提供包含图种的完整风格编号')
    kind = normalize_type(data, kind)
    spec = data['types'][kind]
    if style is None:
        if version:
            raise ValueError('单独提供版本不确定风格，请同时指定 style')
        return resolve(root, kind, spec['default'], line_style=line_style)
    style = style.strip().casefold()
    candidates = [item for item in data['profiles'] if item['type'] == kind and
                  style in [a.strip().casefold() for a in [item['id'], item['name']] + item.get('aliases', [])]]
    styles = {item['id'] for item in candidates}
    if len(styles) != 1:
        options = sorted({item['id'] for item in data['profiles'] if item['type'] == kind})
        raise ValueError(f'未知或歧义风格：{style}；{kind} 可选 {options}')
    style_id = next(iter(styles))
    pinned = version or spec['style_versions'].get(style_id)
    matches = [item for item in candidates if item['version'] == pinned]
    if len(matches) != 1:
        raise ValueError(f'未注册或未固定版本：{kind}/{style_id}@{pinned}；不会自动选择 latest')
    item = matches[0]
    selected_files = [item[field] for field in ('common_spec', 'semantic_spec', 'spec', 'tokens', 'example')]
    lock_path = Path(root) / 'catalog.lock.json'
    if not lock_path.is_file():
        raise ValueError('缺少冻结基线，技能包尚未完成验证')
    lock = read_json(lock_path, '冻结基线')
    if errors := line_style_errors(root, data, lock):
        raise ValueError('\n'.join(errors))
    if errors := interaction_standard_errors(root, data, lock):
        raise ValueError('\n'.join(errors))
    selected_line = normalize_line_style(data, line_style)
    for code, key in lock.get('style_numbers', {}).items():
        if data.get('style_numbers', {}).get(code) != key:
            raise ValueError(f'冻结编号绑定已改变或删除：{code}')
    locked_type = lock.get('types', {}).get(kind, {})
    if spec['default'] != locked_type.get('default', spec['default']):
        raise ValueError(f'冻结默认风格已改变：{kind}')
    if style_id in locked_type.get('style_versions', {}) and spec['style_versions'][style_id] != locked_type['style_versions'][style_id]:
        raise ValueError(f'冻结默认版本已改变：{kind}/{style_id}')
    locked_profile = lock['profiles'].get(profile_key(item))
    if locked_profile is not None and locked_profile != item:
        raise ValueError('冻结风格的解析映射已改变')
    guide = data['types'][kind].get('guide')
    guide_path = None
    if guide is not None:
        guide_path = str(local_file(root, guide))
    selected_files.append(data['line_styles']['spec'])
    interaction = data['interaction_standard']
    selected_files.extend((interaction['spec'], interaction['example']))
    for relative in CORE_FILES + selected_files:
        if relative in lock['files'] and digest(local_file(root, relative)) != lock['files'][relative]:
            raise ValueError(f'冻结依赖被修改：{relative}')
    result = {**item, 'style': item['id'], 'key': profile_key(item),
              'number': style_number(data, profile_key(item)),
              'line_style': selected_line,
              'line_style_version': data['line_styles']['version'],
              'line_spec_path': str(local_file(root, data['line_styles']['spec'])),
              'interaction_standard': interaction['id'],
              'interaction_standard_version': interaction['version'],
              'interaction_spec_path': str(local_file(root, interaction['spec'])),
              'interaction_example_path': str(local_file(root, interaction['example'])),
              'frozen': locked_profile is not None,
              'dependency_hashes': {relative: digest(local_file(root, relative)) for relative in CORE_FILES + selected_files},
              'common_path': str(local_file(root, item['common_spec'])),
              'type_spec_path': str(local_file(root, item['semantic_spec'])),
              'spec_path': str(local_file(root, item['spec'])),
              'tokens_path': str(local_file(root, item['tokens'])),
              'example_path': str(local_file(root, item['example']))}
    if guide_path is not None:
        result['type_guide_path'] = guide_path
    return result


def digest(file):
    # 冻结摘要按 LF 规范化字节计算，不受 core.autocrlf 在不同平台造成的行尾转换影响
    return hashlib.sha256(file.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def validate(root, check_lock=True):
    root = Path(root)
    issues = []
    try:
        index = read_index(root)
        data = compose_catalog(root, index, issues)
        lock_path = root / 'catalog.lock.json'
        lock = read_json(lock_path, '冻结基线') if check_lock and lock_path.is_file() else None
        if check_lock and lock is None:
            issues.append('缺少冻结兼容性基线 catalog.lock.json')
        if not data['line_styles']:
            issues.append('缺少线条样式注册 line_styles')
        else:
            issues.extend(line_style_errors(root, data, lock))
        if not data['interaction_standard']:
            issues.append('缺少交互规范注册 interaction_standard')
        else:
            issues.extend(interaction_standard_errors(root, data, lock))
        keys = {profile_key(item): item for item in data['profiles']}
        for kind, item in data['types'].items():
            if item['default'] not in keys or keys[item['default']]['type'] != kind:
                issues.append(f'默认风格不存在或图种错误：{kind}')
            for style, version in item['style_versions'].items():
                if f'{kind}/{style}@{version}' not in keys:
                    issues.append(f'风格固定版本不存在：{kind}/{style}@{version}')
            for profile in data['profiles']:
                if profile['type'] == kind and profile['id'] not in item['style_versions']:
                    issues.append(f'新增风格未声明固定版本：{kind}/{profile["id"]}')
        numbered = set()
        for code, key in data.get('style_numbers', {}).items():
            if not STYLE_NUMBER.fullmatch(code):
                issues.append(f'非法风格编号：{code}')
            if key not in keys:
                issues.append(f'编号指向未注册风格：{code}')
            if key in numbered:
                issues.append(f'同一风格版本存在多个编号：{key}')
            numbered.add(key)
        if index.get('types'):
            known_types = set(index['types'])
            for path in sorted((root / 'registry' / 'types').glob('*.json')):
                if path.stem not in known_types:
                    issues.append(f'未登记在索引中的图种定义：{path.name}')
            registered = set(keys)
            for path in sorted((root / 'styles').glob('*/*/*')):
                if path.is_dir() and VERSION.fullmatch(path.name):
                    key = f'{path.parent.parent.name}/{path.parent.name}@{path.name}'
                    if key not in registered:
                        issues.append(f'未注册的风格目录：{key}')
        if lock is not None:
            for relative, expected in lock['files'].items():
                try:
                    if digest(local_file(root, relative)) != expected:
                        issues.append(f'冻结资源被修改：{relative}；请新建版本')
                except ValueError as exc:
                    issues.append(str(exc))
            for kind, locked in lock['types'].items():
                current = data['types'].get(kind)
                if current is None:
                    issues.append(f'冻结图种被删除：{kind}')
                    continue
                for field in ('default', 'spec', 'aliases'):
                    if current.get(field) != locked.get(field):
                        issues.append(f'冻结图种默认/规范/别名被修改：{kind} {field}')
                for style, version in locked.get('style_versions', {}).items():
                    if current['style_versions'].get(style) != version:
                        issues.append(f'冻结风格默认版本被修改：{kind}/{style}')
            for key, locked in lock['profiles'].items():
                if keys.get(key) != locked:
                    issues.append(f'冻结风格注册或别名被修改：{key}')
            for code, key in lock.get('style_numbers', {}).items():
                if data.get('style_numbers', {}).get(code) != key:
                    issues.append(f'冻结风格编号被修改或删除：{code}')
    except (KeyError, TypeError, ValueError, OSError) as exc:
        issues.append(str(exc))
    return issues


def make_lock(root, append=False):
    root = Path(root)
    lock_path = root / 'catalog.lock.json'
    if append and not lock_path.exists():
        raise ValueError('追加冻结基线前必须已有基线')
    if not append and lock_path.exists():
        raise ValueError('基线已存在，禁止覆盖；新增版本使用 lock --append')
    errors = validate(root, check_lock=append)
    if errors:
        raise ValueError('\n'.join(errors))
    data = read_catalog(root)
    files = {data['common'], *CORE_FILES} | {item['spec'] for item in data['types'].values()}
    for item in data['profiles']:
        files.update(item[field] for field in ('spec', 'tokens', 'example'))
        files.update((item['common_spec'], item['semantic_spec']))
    files.add(data['line_styles']['spec'])
    files.update(data['interaction_standard'][field] for field in ('spec', 'example'))
    lock = {'schema_version': 1, 'types': data['types'],
            'profiles': {profile_key(item): item for item in data['profiles']},
            'style_numbers': data.get('style_numbers', {}),
            'line_styles': data['line_styles'],
            'interaction_standard': data['interaction_standard'],
            'files': {relative: digest(local_file(root, relative)) for relative in sorted(files)}}
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return {'locked_profiles': len(lock['profiles']), 'locked_files': len(lock['files'])}


def line_preview(ident):
    routes = {
        'orthogonal': 'M120 200 H260 V350 H400',
        'rounded-orthogonal': 'M120 200 H242 Q260 200 260 218 V332 Q260 350 278 350 H400',
        'curved': 'M120 200 C260 200 260 350 400 350',
    }
    if ident not in routes:
        return '<p>此选项的几何示例见线条规范。</p>'
    prefix = f'line-demo-{ident}'
    nodes = ''.join(f'<rect x="{x}" y="{y}" width="100" height="60" rx="12" fill="#EDF3FA" stroke="#95B0C5" stroke-width="1.6"/>'
                    for x, y in ((20, 40), (400, 40), (20, 170), (400, 320)))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="520" height="410" viewBox="0 0 520 410" aria-label="{ident} 线条示意">'
            f'<defs><marker id="{prefix}-arrow" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto">'
            '<path d="M1 1 L9 5 L1 9 Z" fill="#7C909E"/></marker></defs>'
            '<rect width="520" height="410" fill="white"/>'
            f'<g fill="none" stroke="#7C909E" stroke-width="1.6" marker-end="url(#{prefix}-arrow)">'
            '<path data-diagram-role="connector" d="M120 70 H400"/>'
            f'<path data-diagram-role="connector" d="{routes[ident]}"/></g>{nodes}'
            '<g font-family="Microsoft YaHei,sans-serif" font-size="20" fill="#174C7B" text-anchor="middle">'
            '<text x="260" y="40">共线直连</text><text x="260" y="145">非共线连接</text>'
            '<text x="70" y="78">A</text><text x="450" y="78">B</text>'
            '<text x="70" y="208">A</text><text x="450" y="358">B</text></g></svg>')


def gallery(root, output):
    data = read_catalog(root)
    index_path = Path(root) / 'assets/reference-examples/index.json'
    references = json.loads(index_path.read_text(encoding='utf-8')) if index_path.exists() else {}
    if not isinstance(references, dict):
        raise ValueError('原始样例索引必须是 profile key 到图片路径的映射')
    known = {profile_key(item) for item in data['profiles']}
    preview_index = Path(root) / 'assets/gallery-examples/index.json'
    preview_paths = json.loads(preview_index.read_text(encoding='utf-8')) if preview_index.exists() else {}
    if not isinstance(preview_paths, dict):
        raise ValueError('展示样例索引必须是 profile key 到 SVG 路径的映射')
    previews = {}
    for key, relative in preview_paths.items():
        if key not in known or not isinstance(relative, str):
            raise ValueError(f'展示样例关联无效：{key}')
        if Path(relative).suffix.lower() != '.svg':
            raise ValueError(f'展示样例必须为 SVG：{relative}')
        content = local_file(root, relative).read_text(encoding='utf-8')
        try:
            svg = ET.fromstring(content)
        except ET.ParseError as exc:
            raise ValueError(f'展示样例不是有效 SVG：{relative}') from exc
        if svg.tag.rsplit('}', 1)[-1] != 'svg':
            raise ValueError(f'展示样例根节点不是 SVG：{relative}')
        for element in svg.iter():
            if element.tag.rsplit('}', 1)[-1] in ('script', 'foreignObject'):
                raise ValueError(f'展示样例包含不支持的元素：{relative}')
            for attr, value in element.attrib.items():
                if attr.lower().startswith('on') or (attr.rsplit('}', 1)[-1] == 'href' and not value.startswith(('#', 'data:image/'))):
                    raise ValueError(f'展示样例包含外部引用或事件：{relative}')
        metadata = next((el for el in svg.iter() if el.tag.rsplit('}', 1)[-1] == 'metadata'), None)
        if metadata is not None and metadata.text:
            try:
                profile = json.loads(metadata.text).get('profile')
            except (json.JSONDecodeError, AttributeError) as exc:
                raise ValueError(f'展示样例元数据无效：{relative}') from exc
            if profile != key:
                raise ValueError(f'展示样例归属与 profile 不一致：{relative}')
        previews[key] = content
    originals = {}
    for key, relative in references.items():
        if key not in known or not isinstance(relative, str):
            raise ValueError(f'原始样例关联无效：{key}')
        if Path(relative).suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp'):
            raise ValueError(f'不支持的原始样例格式：{relative}')
        image = local_file(root, relative)
        mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp'}[image.suffix.lower()]
        originals[key] = f'data:{mime};base64,' + base64.b64encode(image.read_bytes()).decode('ascii')
    sections, navigation = [], []
    for kind, info in data['types'].items():
        items = [item for item in data['profiles'] if item['type'] == kind]
        if not items:
            continue
        items.sort(key=lambda item: (style_number(data, profile_key(item)) or 'ZZZ', profile_key(item)))
        type_name = html.escape(info['name'])
        child_links = ''.join(f'<a class="nav-child" href="#style-{style_number(data, profile_key(item))}">'
                              f'{style_number(data, profile_key(item))} {html.escape(item["name"])}</a>' for item in items)
        navigation.append(f'<div class="nav-group"><a class="nav-heading" href="#type-{kind}">{type_name}<span>{len(items)}</span></a>{child_links}</div>')
        cards = []
        for item in items:
            key = profile_key(item)
            code = style_number(data, key)
            if code is None:
                raise ValueError(f'生成预览前请为新增风格分配固定编号：{key}')
            example = previews[key] if key in previews else local_file(root, item['example']).read_text(encoding='utf-8')
            default = '<span class="default">默认风格</span>' if key == info['default'] else ''
            original = (f'<button type="button" class="original-button" data-original="{originals[key]}" '
                        f'data-title="{code} {html.escape(item["name"], quote=True)} · 原始样例图">查看原始样例图</button>'
                        if key in originals else '')
            cards.append(f'<article id="style-{code}" data-style-number="{code}">'
                         f'<div class="card-top"><div class="card-title"><span class="number">{code}</span><h3>{html.escape(item["name"])}</h3></div><div class="card-actions">{original}{default}</div></div>'
                         f'<button type="button" class="preview" data-preview aria-label="放大查看 {code} 示例图">{example}</button>'
                         f'<div class="invocation"><span>调用示例</span><code>使用 {code} 风格绘制{type_name}</code><code class="profile">{html.escape(key)}</code></div></article>')
        sections.append(f'<section id="type-{kind}" aria-labelledby="heading-{kind}">'
                        f'<div class="section-heading"><h2 id="heading-{kind}">{type_name}</h2>'
                        f'<span>{len(items)} 种风格</span></div><div class="cards">' + ''.join(cards) + '</div></section>')
    legend = []
    for kind, info in data['types'].items():
        prefixes = sorted({code.rsplit('-', 1)[0] for code, key in data.get('style_numbers', {}).items()
                           if key.startswith(kind + '/')})
        if prefixes:
            legend.append(html.escape(' / '.join(prefixes) + ' = ' + info['name']))
    if errors := line_style_errors(root, data):
        raise ValueError('\n'.join(errors))
    lines = data['line_styles']
    line_cards = []
    for ident, item in lines['options'].items():
        default = '（默认）' if ident == lines['default'] else ''
        line_cards.append(f'<article id="line-{html.escape(ident)}" data-line-style="{html.escape(ident)}"><h3>{html.escape(item["name"])}{default}</h3>'
                          f'<code class="profile">{html.escape(ident)} · {html.escape(lines["version"])}</code>'
                          f'<button type="button" class="preview" data-preview aria-label="放大查看{html.escape(item["name"])}示例">{line_preview(ident)}</button></article>')
    line_section = ('<section id="line-styles" aria-labelledby="heading-lines"><div class="section-heading">'
                    '<h2 id="heading-lines">线条样式</h2><span>与下方视觉风格独立组合</span></div>'
                    '<p>明显可以直线连接时直接连接；必要转折再使用所选线条。圆角折线使用真实圆弧或贝塞尔转角。</p>'
                    '<p>组合示例：<code>绘制流程图，样式 FC-01（或浅色业务流程），线条样式圆角折线</code>。</p>'
                    '<div class="cards line-cards">' + ''.join(line_cards) + '</div></section>')
    line_links = ''.join(f'<a class="nav-child" href="#line-{html.escape(ident)}">{html.escape(item["name"])}</a>'
                         for ident, item in lines['options'].items())
    navigation.insert(0, f'<div class="nav-group"><a class="nav-heading" href="#line-styles">线条样式<span>{len(line_cards)}</span></a>{line_links}</div>')
    if errors := interaction_standard_errors(root, data):
        raise ValueError('\n'.join(errors))
    interaction = data['interaction_standard']
    interaction_example = local_file(root, interaction['example']).read_text(encoding='utf-8')
    interaction_section = ('<section id="interaction-standards" aria-labelledby="heading-interactions">'
        '<div class="section-heading"><h2 id="heading-interactions">单向交互规范</h2>'
        f'<span>{html.escape(interaction["version"])} · 与视觉和线条独立</span></div>'
        '<p>每条有向线只保留一个方向；请求用实线，虚线返回与确认独立布线。业务回调仍是独立实线请求。</p>'
        '<p>系统边界独立、同层对齐；短路径少转折，必要交叉用圆弧且不表示连接；完整逻辑编号。</p>'
        '<div class="cards wide"><article><h3>通用交互示例</h3>'
        f'<button type="button" class="preview" data-preview aria-label="放大查看通用交互示例">{interaction_example}</button></article></div></section>')
    navigation.insert(0, '<div class="nav-group"><a class="nav-heading" href="#interaction-standards">交互规范<span>1</span></a></div>')
    template = (Path(root) / 'assets/gallery-shell.html').read_text(encoding='utf-8')
    page = (template.replace('{{NAVIGATION}}', ''.join(navigation))
            .replace('{{CONTENT}}', interaction_section + line_section + ''.join(sections))
            .replace('{{LEGEND}}', ' · '.join(legend)))
    Path(output).write_text(page, encoding='utf-8')
    return {'output': str(output), 'profiles': len(data['profiles']), 'groups': len(sections)}


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    sub = parser.add_subparsers(dest='command', required=True)
    listing = sub.add_parser('list')
    listing_group = listing.add_mutually_exclusive_group()
    listing_group.add_argument('--type')
    listing_group.add_argument('--line-styles', action='store_true', help='列出独立线条样式')
    selection = sub.add_parser('resolve')
    selection.add_argument('--type')
    selection.add_argument('--style')
    selection.add_argument('--version')
    selection.add_argument('--number', help='固定风格编号，例如 ST-01；无需另填图种')
    selection.add_argument('--line-style', help='线条样式 ID 或名称：直角折线 / 圆角折线 / 直连曲线')
    sub.add_parser('validate')
    locking = sub.add_parser('lock')
    locking.add_argument('--append', action='store_true')
    generating = sub.add_parser('gallery')
    generating.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'list':
            data = read_catalog(args.root)
            kind = normalize_type(data, args.type) if args.type else None
            result = [{'number': style_number(data, profile_key(item)), 'key': profile_key(item), 'name': item['name'],
                       'default': data['types'][item['type']]['default'] == profile_key(item)}
                      for item in data['profiles'] if kind is None or item['type'] == kind]
            if args.line_styles:
                if errors := line_style_errors(args.root, data):
                    raise ValueError('\n'.join(errors))
                lines = data['line_styles']
                result = [{'id': ident, 'name': item['name'], 'version': lines['version'],
                           'default': ident == lines['default']} for ident, item in lines['options'].items()]
        elif args.command == 'resolve':
            result = resolve(args.root, args.type, args.style, args.version, args.number, args.line_style)
        elif args.command == 'validate':
            result = {'valid': not (errors := validate(args.root)), 'errors': errors}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result['valid'] else 1
        elif args.command == 'lock':
            result = make_lock(args.root, args.append)
        else:
            result = gallery(args.root, args.output)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stdout)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
