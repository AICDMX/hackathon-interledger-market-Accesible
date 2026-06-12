from django.test import TestCase
from jobs.templatetags.job_tags import language_name, status_badge, status_color, status_bg


class LanguageNameFilterTest(TestCase):
    def test_known_codes(self):
        self.assertEqual(language_name("nah"), "Náhuatl")
        self.assertEqual(language_name("oto"), "Otomí (Hñähñu)")
        self.assertEqual(language_name("tzo"), "Tsotsil")
        self.assertEqual(language_name("que"), "Quechua")
        self.assertEqual(language_name("zai"), "Zapoteco")
        self.assertEqual(language_name("cak"), "Kaqchikel")
        self.assertEqual(language_name("aym"), "Aymara")
        self.assertEqual(language_name("gn"), "Guaraní")
        self.assertEqual(language_name("chj"), "Chinanteco")
        self.assertEqual(language_name("trs"), "Triqui")
        self.assertEqual(language_name("en"), "English")
        self.assertEqual(language_name("es"), "Español")

    def test_unknown_code_returns_code(self):
        self.assertEqual(language_name("xyz"), "xyz")
        self.assertEqual(language_name(""), "")

    def test_all_demo_languages_have_names(self):
        demo_codes = [
            "nah", "oto", "que", "tzo", "zai", "cak", "aym",
            "maz", "trs", "chj", "mxt", "yua", "pua", "gn",
        ]
        for code in demo_codes:
            result = language_name(code)
            self.assertNotEqual(result, code, f"{code} has no display name")


class StatusBadgeFilterTest(TestCase):
    def test_returns_html_span(self):
        result = status_badge("recruiting")
        self.assertIn("<span", result)
        self.assertIn("Recruiting", result)
        self.assertIn("</span>", result)

    def test_known_statuses_have_colors(self):
        statuses = [
            "draft", "recruiting", "selecting", "submitting",
            "reviewing", "expired", "canceled", "complete",
            "pending", "selected", "accepted", "rejected",
        ]
        for status in statuses:
            result = status_badge(status)
            self.assertIn("background:", result)
            self.assertIn("color:", result)

    def test_unknown_status_gets_default_colors(self):
        result = status_badge("unknown")
        self.assertIn("#64748b", result)  # default gray
        self.assertIn("Unknown", result)

    def test_underscores_become_spaces(self):
        result = status_badge("in_progress")
        self.assertIn("In Progress", result)


class StatusColorFilterTest(TestCase):
    def test_returns_color(self):
        self.assertEqual(status_color("recruiting"), "#15803d")
        self.assertEqual(status_color("complete"), "#166534")

    def test_unknown_returns_default(self):
        self.assertEqual(status_color("nope"), "#64748b")


class StatusBgFilterTest(TestCase):
    def test_returns_bg(self):
        self.assertEqual(status_bg("recruiting"), "#dcfce7")
        self.assertEqual(status_bg("rejected"), "#fee2e2")

    def test_unknown_returns_default(self):
        self.assertEqual(status_bg("nope"), "#f1f5f9")
