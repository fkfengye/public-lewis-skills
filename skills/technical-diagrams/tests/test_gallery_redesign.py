import base64
import importlib.util
import json
from pathlib import Path
import shutil
import uuid
import unittest


ROOT = Path(__file__).resolve().parents[1]


class GalleryRedesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('gallery_catalog', ROOT / 'scripts/catalog.py')
        cls.catalog = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.catalog)

    def setUp(self):
        scratch = ROOT.parents[1] / '.data-cache' / 'technical-diagrams-tests'
        scratch.mkdir(parents=True, exist_ok=True)
        self.root = scratch / ('gallery-test-' + uuid.uuid4().hex)
        def cleanup():
            self.assertEqual(self.root.resolve().parent, scratch.resolve())
            shutil.rmtree(self.root)
        self.addCleanup(cleanup)
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('__pycache__', 'node_modules'))
        self.output = self.root / 'assets' / 'test-gallery.html'

    def test_sidebar_previews_and_authorized_original_are_generated(self):
        self.catalog.gallery(self.root, self.output)
        page = self.output.read_text(encoding='utf-8')
        self.assertIn('aria-label="风格目录"', page)
        self.assertIn('href="#type-architecture"', page)
        self.assertIn('href="#style-AR-06"', page)
        self.assertIn('href="#line-rounded-orthogonal"', page)
        self.assertIn('id="line-rounded-orthogonal"', page)
        self.assertIn('id="image-viewer"', page)
        self.assertIn('data-preview', page)
        original_card = page.split('data-style-number="AR-06"', 1)[1].split('</article>', 1)[0]
        other_card = page.split('data-style-number="AR-05"', 1)[1].split('</article>', 1)[0]
        self.assertIn('查看原始样例图', original_card)
        self.assertIn('data:image/png;base64,', original_card)
        encoded = original_card.split('data:image/png;base64,', 1)[1].split('"', 1)[0]
        self.assertEqual(base64.b64decode(encoded), (self.root / 'assets/reference-examples/ar-06-original.png').read_bytes())
        self.assertNotIn('查看原始样例图', other_card)
        self.catalog.gallery(self.root, self.output)
        self.assertEqual(self.output.read_text(encoding='utf-8'), page)

    def test_invalid_original_reference_fails_generation(self):
        index = self.root / 'assets/reference-examples/index.json'
        index.parent.mkdir(parents=True, exist_ok=True)
        for path in ('../outside.png', 'assets/reference-examples/missing.png'):
            with self.subTest(path=path):
                index.write_text(json.dumps({'architecture/blue-green-detailed@1.0.0': path}), encoding='utf-8')
                with self.assertRaises(ValueError):
                    self.catalog.gallery(self.root, self.output)
        index.write_text(json.dumps({'architecture/not-registered@1.0.0': 'assets/reference-examples/ar-06-original.png'}), encoding='utf-8')
        with self.assertRaises(ValueError):
            self.catalog.gallery(self.root, self.output)

    def test_style_name_is_in_header_and_profile_key_is_in_footer(self):
        self.catalog.gallery(self.root, self.output)
        page = self.output.read_text(encoding='utf-8')
        card = page.split('data-style-number="AR-06"', 1)[1].split('</article>', 1)[0]
        self.assertIn('<div class="card-title"><span class="number">AR-06</span><h3>蓝绿密集细节</h3></div>', card)
        self.assertGreater(card.index('<code class="profile">architecture/blue-green-detailed@1.0.0</code>'), card.index('调用示例'))

    def test_gallery_uses_indexed_feature_preview_without_changing_profile(self):
        key = 'architecture/cross-boundary-layers@1.0.0'
        index = self.root / 'assets/gallery-examples/index.json'
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(json.dumps({key: 'styles/architecture/cross-boundary-layers/1.0.0/feature-atlas.svg'}), encoding='utf-8')
        fixed = self.catalog.resolve(self.root, None, number='AR-08')
        self.catalog.gallery(self.root, self.output)
        page = self.output.read_text(encoding='utf-8')
        card = page.split('data-style-number="AR-08"', 1)[1].split('</article>', 1)[0]
        preview = (self.root / 'styles/architecture/cross-boundary-layers/1.0.0/feature-atlas.svg').read_text(encoding='utf-8')
        self.assertTrue(preview in card, 'AR-08 卡片应展示完整特征图')
        self.assertFalse(Path(fixed['example_path']).read_text(encoding='utf-8') in card)
        self.assertTrue(fixed['example_path'].replace('\\', '/').endswith('/cross-boundary-layers/1.0.0/example.svg'))
        self.assertIn('查看原始样例图', card)
        other = page.split('data-style-number="AR-07"', 1)[1].split('</article>', 1)[0]
        other_example = self.catalog.resolve(self.root, None, number='AR-07')['example_path']
        self.assertTrue(Path(other_example).read_text(encoding='utf-8') in other)

    def test_invalid_gallery_example_index_is_rejected(self):
        index = self.root / 'assets/gallery-examples/index.json'
        index.parent.mkdir(parents=True, exist_ok=True)
        key = 'architecture/cross-boundary-layers@1.0.0'
        invalid = ({key: '../outside.svg'}, {key: 'references/missing.svg'},
                   {key: 'assets/reference-examples/ar-08-original.png'},
                   {'architecture/unknown@1.0.0': 'styles/architecture/cross-boundary-layers/1.0.0/feature-atlas.svg'})
        for item in invalid:
            with self.subTest(item=item):
                index.write_text(json.dumps(item), encoding='utf-8')
                with self.assertRaises(ValueError):
                    self.catalog.gallery(self.root, self.output)

        candidate = self.root / 'references/bad-preview.svg'
        for content in ('<svg><script/></svg>', '<svg><image href="https://example.com/image.png"/></svg>',
                        '<svg><metadata>{"profile":"wrong"}</metadata></svg>', '<svg'):
            with self.subTest(content=content):
                candidate.write_text(content, encoding='utf-8')
                index.write_text(json.dumps({key: 'references/bad-preview.svg'}), encoding='utf-8')
                with self.assertRaises(ValueError):
                    self.catalog.gallery(self.root, self.output)


if __name__ == '__main__':
    unittest.main()
