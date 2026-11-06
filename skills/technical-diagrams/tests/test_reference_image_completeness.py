from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReferenceImageGuidanceTests(unittest.TestCase):
    def test_reference_routes_cover_one_off_and_extension(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('references/reference-image-completeness.md', skill)
        self.assertIn('普通参考图分析、复刻和扩展', skill)
        self.assertIn('参考图扩展工作流', skill)
        self.assertTrue((ROOT / 'references/reference-image-completeness.md').is_file())

    def test_missing_features_and_uncertainty_are_explicit(self):
        guide = (ROOT / 'references/reference-image-completeness.md').read_text(encoding='utf-8')
        for phrase in ('已覆盖', '部分覆盖', '未覆盖', '不适用', '待确认', '用户明确要求简化', '不可辨认', '不能证明视觉相似', '未绘制'):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, guide)
        for phrase in ('云', '字体', '标签', '箭头', '嵌套'):
            with self.subTest(feature=phrase):
                self.assertIn(phrase, guide)

    def test_original_reference_consent_is_explicit_and_scoped(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        extension = (ROOT / 'references/reference-image-extension-workflow.md').read_text(encoding='utf-8')
        for text in (skill, extension):
            with self.subTest(source='skill' if text is skill else 'extension'):
                self.assertIn('主动询问', text)
                self.assertIn('随技能目录和生成的预览一起分发', text)
                self.assertIn('未获明确授权', text)
                self.assertIn('无需重复询问', text)
        self.assertIn('仅授权展示而未授权保存原文件时不得在技能内另存', extension)
        self.assertIn('等待答复期间继续不依赖授权的分析和通用示例', extension)


if __name__ == '__main__':
    unittest.main()
