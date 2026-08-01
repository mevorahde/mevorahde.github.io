from __future__ import annotations

import json
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import verify_site  # noqa: E402


class PortfolioSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.parser, cls.html = verify_site.parse_html()

    def test_complete_verification(self) -> None:
        self.assertEqual(verify_site.run_checks(), [])

    def test_semantic_structure_and_heading_order(self) -> None:
        self.assertEqual(self.parser.errors, [])
        self.assertEqual(self.parser.headings.count(1), 1)
        self.assertEqual(self.parser.headings[0], 1)
        for previous, current in zip(self.parser.headings, self.parser.headings[1:]):
            self.assertLessEqual(current, previous + 1)
        tags = [tag for tag, _ in self.parser.tags]
        for landmark in ("header", "nav", "main", "footer"):
            self.assertIn(landmark, tags)

    def test_navigation_and_local_paths_resolve(self) -> None:
        for link in self.parser.links:
            href = link["href"]
            if href.startswith("#"):
                self.assertIn(href[1:], self.parser.ids)
            elif "://" not in href:
                self.assertTrue((ROOT / href.split("#", 1)[0]).is_file())
        for image in self.parser.images:
            self.assertTrue((ROOT / image["src"]).is_file())

    def test_outbound_repository_urls_use_exact_canonical_spellings(self) -> None:
        expected = {
            "https://github.com/mevorahde/sql-password-locker",
            "https://github.com/mevorahde/project-creation-automation",
            "https://github.com/mevorahde/NFL_Pool_Automation",
            "https://github.com/mevorahde/morning-app-launcher",
            "https://github.com/mevorahde/hyphy-oregon-conference-generator",
            "https://github.com/mevorahde/pw_locker",
            "https://github.com/mevorahde/Git_Cheat_Sheet",
        }
        repository_urls = {
            link["href"]
            for link in self.parser.links
            if link.get("href", "").startswith(
                "https://github.com/mevorahde/"
            )
            and link["href"] != verify_site.GITHUB_PROFILE_URL
        }
        self.assertEqual(verify_site.APPROVED_REPOSITORY_URLS, expected)
        self.assertEqual(repository_urls, expected)

    def test_json_ld_is_exactly_the_approved_person_record(self) -> None:
        self.assertEqual(len(self.parser.scripts), 1)
        record = json.loads(self.parser.scripts[0]["data"])
        self.assertEqual(
            record,
            {
                "@context": "https://schema.org",
                "@type": "Person",
                "name": "David Mevorah",
                "jobTitle": "Healthcare integration engineer",
                "url": verify_site.CANONICAL_URL,
                "sameAs": [verify_site.GITHUB_PROFILE_URL, verify_site.LINKEDIN_URL],
            },
        )

    def test_social_metadata_is_exact_and_consistent(self) -> None:
        canonical = [
            attrs.get("href")
            for tag, attrs in self.parser.tags
            if tag == "link" and attrs.get("rel") == "canonical"
        ]
        self.assertEqual(canonical, [verify_site.CANONICAL_URL])

        og = {
            item.get("property"): item.get("content")
            for item in self.parser.metas
            if item.get("property")
        }
        self.assertEqual(
            og,
            {
                "og:title": verify_site.SOCIAL_TITLE,
                "og:description": verify_site.SOCIAL_DESCRIPTION,
                "og:type": "website",
                "og:url": verify_site.CANONICAL_URL,
                "og:image": verify_site.SOCIAL_IMAGE_URL,
                "og:image:width": "1200",
                "og:image:height": "630",
                "og:image:alt": verify_site.SOCIAL_IMAGE_ALT,
            },
        )
        by_name = {
            item.get("name"): item.get("content")
            for item in self.parser.metas
            if item.get("name")
        }
        twitter = {
            name: by_name.get(name)
            for name in (
                "twitter:card",
                "twitter:title",
                "twitter:description",
                "twitter:image",
                "twitter:image:alt",
            )
        }
        self.assertEqual(
            twitter,
            {
                "twitter:card": "summary_large_image",
                "twitter:title": verify_site.SOCIAL_TITLE,
                "twitter:description": verify_site.SOCIAL_DESCRIPTION,
                "twitter:image": verify_site.SOCIAL_IMAGE_URL,
                "twitter:image:alt": verify_site.SOCIAL_IMAGE_ALT,
            },
        )
        self.assertTrue(og["og:description"])
        self.assertEqual(og["og:description"], twitter["twitter:description"])
        self.assertEqual(self.html.count(verify_site.SOCIAL_IMAGE_URL), 2)

    def test_social_png_is_unique_valid_sanitized_and_fixed(self) -> None:
        matching = [
            path
            for path in ROOT.rglob("david-mevorah-portfolio-social-preview.png")
            if path.is_file()
        ]
        self.assertEqual(matching, [ROOT / verify_site.SOCIAL_IMAGE_PATH])
        path = matching[0]
        details = verify_site.inspect_png(path)
        self.assertEqual((details["width"], details["height"]), (1200, 630))
        self.assertEqual((details["bit_depth"], details["color_type"]), (8, 2))
        self.assertEqual(set(details["chunks"]), {"IHDR", "IDAT", "IEND"})
        self.assertEqual(
            verify_site.sha256(path),
            verify_site.SOCIAL_IMAGE["sha256"],
        )

    def test_screenshots_match_approved_hashes_and_dimensions(self) -> None:
        for relative, expected in verify_site.SCREENSHOTS.items():
            path = ROOT / relative
            self.assertEqual(verify_site.sha256(path), expected["sha256"])
            self.assertEqual(
                verify_site.png_dimensions(path),
                (expected["width"], expected["height"]),
            )

    def test_no_executable_or_external_runtime_content(self) -> None:
        tags = [tag for tag, _ in self.parser.tags]
        for forbidden in ("form", "iframe", "object", "embed", "video", "audio", "canvas"):
            self.assertNotIn(forbidden, tags)
        self.assertNotIn("target=\"_blank\"", self.html)
        self.assertFalse(any(path.suffix == ".js" for path in ROOT.rglob("*") if path.is_file()))

    def test_sitemap_and_robots_parse(self) -> None:
        tree = ET.parse(ROOT / "sitemap.xml")
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        self.assertEqual(
            [node.text for node in tree.findall("s:url/s:loc", namespace)],
            [verify_site.CANONICAL_URL],
        )
        self.assertEqual(
            (ROOT / "robots.txt").read_text(encoding="utf-8"),
            "User-agent: *\nAllow: /\nSitemap: https://mevorahde.github.io/sitemap.xml\n",
        )

    def test_exact_intended_file_inventory(self) -> None:
        self.assertEqual(verify_site.project_files(), verify_site.EXPECTED_FILES)


if __name__ == "__main__":
    unittest.main()
