"""Tests for render.py — focused on the sources-rendering change."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import render  # noqa: E402


class RenderSourcesConsultedTests(unittest.TestCase):
    def test_list_of_dicts_renders_as_linked_dot_separated_html(self):
        sources = [
            {"name": "BBC", "url": "https://www.bbc.com/news"},
            {"name": "DW", "url": "https://www.dw.com/en/top-stories/s-9097"},
        ]
        html = render.render_sources_consulted(sources)

        self.assertIn('href="https://www.bbc.com/news"', html)
        self.assertIn(">BBC</a>", html)
        self.assertIn('href="https://www.dw.com/en/top-stories/s-9097"', html)
        self.assertIn(">DW</a>", html)
        self.assertIn("&middot;", html)

    def test_empty_list_returns_empty_string(self):
        self.assertEqual(render.render_sources_consulted([]), "")

    def test_legacy_string_passes_through_unchanged(self):
        legacy = "Wikipedia Current Events, BBC, DW, Al Jazeera"
        self.assertEqual(render.render_sources_consulted(legacy), legacy)

    def test_stringified_json_list_is_parsed_and_rendered_as_links(self):
        # Regression: the research agent sometimes serializes sources_consulted
        # as a JSON string instead of a list. It used to leak literal brackets
        # into the email footer; now it should parse and render like a list.
        import json
        stringified = json.dumps([
            {"name": "BBC", "url": "https://www.bbc.com/news"},
            {"name": "CNN", "url": "https://www.cnn.com/world"},
        ])
        html = render.render_sources_consulted(stringified)

        self.assertIn('href="https://www.bbc.com/news"', html)
        self.assertIn(">BBC</a>", html)
        self.assertIn('href="https://www.cnn.com/world"', html)
        self.assertNotIn("[", html)
        self.assertNotIn("{", html)

    def test_list_of_plain_strings_renders_as_spans_without_crashing(self):
        html = render.render_sources_consulted(["BBC", "CNN", "DW"])
        self.assertIn(">BBC</span>", html)
        self.assertIn(">CNN</span>", html)
        self.assertIn("&middot;", html)
        self.assertNotIn("<a ", html)

    def test_malformed_items_fall_back_to_plain_text(self):
        sources = [
            {"name": "BBC", "url": "https://www.bbc.com/news"},
            {"missing": "url_key"},
            "CNN",
        ]
        html = render.render_sources_consulted(sources)
        self.assertIn(">BBC</a>", html)
        self.assertIn(">CNN</span>", html)
        self.assertNotIn("missing", html)


class RenderStoriesSourcesRemovedTests(unittest.TestCase):
    def test_per_story_source_links_not_rendered(self):
        stories = [
            {
                "section": "Middle East & Africa",
                "headline": "Test Story",
                "bullets": ["bullet one", "bullet two"],
                "sources": [
                    {"name": "BBC", "url": "https://www.bbc.com/news"},
                    {"name": "DW", "url": "https://www.dw.com/"},
                ],
            }
        ]
        html = render.render_stories(stories)

        self.assertNotIn('href="https://www.bbc.com/news"', html)
        self.assertNotIn(">BBC</a>", html)
        self.assertNotIn("<a ", html)

    def test_framing_watch_still_rendered(self):
        stories = [
            {
                "section": "Test",
                "headline": "Test",
                "bullets": ["bullet"],
                "framing_watch": "RT emphasizes X; BBC focuses on Y",
            }
        ]
        html = render.render_stories(stories)
        self.assertIn("Framing Watch", html)
        self.assertIn("RT emphasizes X", html)


class RenderEndToEndTests(unittest.TestCase):
    def test_sources_consulted_list_appears_linked_in_footer(self):
        data = {
            "title": "Test Digest",
            "date_range": "Jan 1 2026",
            "summary": ["point one"],
            "stories": [
                {
                    "section": "Foo",
                    "headline": "Bar",
                    "bullets": ["baz"],
                }
            ],
            "sources_consulted": [
                {"name": "BBC", "url": "https://www.bbc.com/news"},
                {"name": "RT", "url": "https://www.rt.com/"},
            ],
        }
        html = render.render("global-weekly", data)

        self.assertIn("Sources consulted", html)
        self.assertIn('href="https://www.bbc.com/news"', html)
        self.assertIn('href="https://www.rt.com/"', html)


if __name__ == "__main__":
    unittest.main()
