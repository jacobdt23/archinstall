"""Unit tests for Orbit Suite apps (Edit, View, Launch, Term)."""

from __future__ import annotations

import unittest

from orbit_suite.launch import LaunchEntry, load_desktop_apps, safe_eval_math, score_match


class TestOrbitSuite(unittest.TestCase):
    def test_safe_eval_math(self) -> None:
        self.assertEqual(safe_eval_math("2 + 2 * 10"), "22")
        self.assertEqual(safe_eval_math("(10 - 4) / 2"), "3")
        self.assertIsNone(safe_eval_math("__import__('os').system('echo hi')"))

    def test_launch_scoring(self) -> None:
        entry = LaunchEntry("Orbit Files", "File Manager", None, "orbit files file manager")
        self.assertEqual(score_match("orbit files", entry), 100)
        self.assertEqual(score_match("orbit", entry), 80)
        self.assertEqual(score_match("files", entry), 60)
        self.assertEqual(score_match("ofls", entry), 20)
        self.assertEqual(score_match("zzzz", entry), 0)

    def test_desktop_app_discovery(self) -> None:
        apps = load_desktop_apps()
        names = {a.name for a in apps}
        self.assertIn("Orbit Files", names)


if __name__ == "__main__":
    unittest.main()
