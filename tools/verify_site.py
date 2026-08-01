#!/usr/bin/env python3
"""Verify the dependency-free portfolio source with the Python standard library."""

from __future__ import annotations

import configparser
import hashlib
import json
import re
import struct
import sys
import xml.etree.ElementTree as ET
import zlib
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_URL = "https://mevorahde.github.io/"
LINKEDIN_URL = "https://www.linkedin.com/in/david-mevorah-engineer/"
GITHUB_PROFILE_URL = "https://github.com/mevorahde"
SOCIAL_TITLE = "David Mevorah | Healthcare Integration Engineer"
SOCIAL_DESCRIPTION = (
    "Secure, testable automation and reliable data workflows with Python, SQL, APIs, and C#."
)
SOCIAL_IMAGE_PATH = "assets/images/david-mevorah-portfolio-social-preview.png"
SOCIAL_IMAGE_URL = CANONICAL_URL + SOCIAL_IMAGE_PATH
SOCIAL_IMAGE_ALT = "David Mevorah — Reliable software for work that needs to hold up."

EXPECTED_FILES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".nojekyll",
    "ASSET_PROVENANCE.md",
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "assets/css/site.css",
    "assets/images/hyphy-oregon-conference-generator-terminal.png",
    "assets/images/morning-app-launcher-interface.png",
    "assets/images/sql-password-locker-interface.png",
    SOCIAL_IMAGE_PATH,
    "index.html",
    "robots.txt",
    "sitemap.xml",
    "tests/test_site.py",
    "tools/verify_site.py",
}

SCREENSHOTS = {
    "assets/images/sql-password-locker-interface.png": {
        "sha256": "402633c3a545041972ca270e3eb298cbe596c7658a4d7e4ae83406bd5618bcf2",
        "width": 895,
        "height": 625,
    },
    "assets/images/morning-app-launcher-interface.png": {
        "sha256": "ebe9f6e9294c17d4b53eee2f42ad3c024f3a34a4b51bea300ca93fe9a393c911",
        "width": 824,
        "height": 524,
    },
    "assets/images/hyphy-oregon-conference-generator-terminal.png": {
        "sha256": "4a9e4bd9a99d367726b44a986e1abd13e9f6331e1adcd3fb31eb16e32a128e9b",
        "width": 582,
        "height": 608,
    },
}

SOCIAL_IMAGE = {
    "sha256": "8764c95d4d4f6698c24d3f86e8e81488c536baa0fb6d59379cc320dbbf794de3",
    "width": 1200,
    "height": 630,
    "bit_depth": 8,
    "color_type": 2,
}

APPROVED_REPOSITORY_URLS = {
    "https://github.com/mevorahde/sql-password-locker",
    "https://github.com/mevorahde/project-creation-automation",
    "https://github.com/mevorahde/NFL_Pool_Automation",
    "https://github.com/mevorahde/morning-app-launcher",
    "https://github.com/mevorahde/hyphy-oregon-conference-generator",
    "https://github.com/mevorahde/pw_locker",
    "https://github.com/mevorahde/Git_Cheat_Sheet",
}

VOID_ELEMENTS = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "param",
    "source",
    "track",
    "wbr",
}


class SiteHTMLParser(HTMLParser):
    """Collect structural evidence while enforcing explicit balanced markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.errors: list[str] = []
        self.stack: list[str] = []
        self.tags: list[tuple[str, dict[str, str]]] = []
        self.ids: set[str] = set()
        self.headings: list[int] = []
        self.links: list[dict[str, str]] = []
        self.images: list[dict[str, str]] = []
        self.metas: list[dict[str, str]] = []
        self.scripts: list[dict[str, str]] = []
        self._active_script: dict[str, str] | None = None
        self._script_data: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name: value or "" for name, value in attrs}
        self.tags.append((tag, attributes))
        if "id" in attributes:
            if attributes["id"] in self.ids:
                self.errors.append(f"duplicate id: {attributes['id']}")
            self.ids.add(attributes["id"])
        if re.fullmatch(r"h[1-6]", tag):
            self.headings.append(int(tag[1]))
        if tag == "a":
            self.links.append(attributes)
        if tag == "img":
            self.images.append(attributes)
        if tag == "meta":
            self.metas.append(attributes)
        if tag == "script":
            self._active_script = attributes
            self._script_data = []
        for name in attributes:
            if name.lower().startswith("on"):
                self.errors.append(f"inline event handler on <{tag}>: {name}")
        if tag not in VOID_ELEMENTS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in VOID_ELEMENTS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            self.errors.append(f"unexpected closing tag: {tag}")
            return
        expected = self.stack.pop()
        if expected != tag:
            self.errors.append(f"closing tag {tag} does not match {expected}")
        if tag == "script" and self._active_script is not None:
            script = dict(self._active_script)
            script["data"] = "".join(self._script_data).strip()
            self.scripts.append(script)
            self._active_script = None
            self._script_data = []

    def handle_data(self, data: str) -> None:
        if self._active_script is not None:
            self._script_data.append(data)

    def close(self) -> None:
        super().close()
        if self.stack:
            self.errors.append("unclosed tags: " + ", ".join(self.stack))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def png_dimensions(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) != 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError(f"not a supported PNG: {path.relative_to(ROOT)}")
    return struct.unpack(">II", data[16:24])


def inspect_png(path: Path) -> dict[str, object]:
    """Validate a non-interlaced PNG and return its structural inventory."""

    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"invalid PNG signature: {path.relative_to(ROOT)}")

    offset = 8
    chunks: list[str] = []
    idat_parts: list[bytes] = []
    ihdr: tuple[int, int, int, int, int, int, int] | None = None
    while offset < len(data):
        if offset + 12 > len(data):
            raise ValueError(f"truncated PNG chunk: {path.relative_to(ROOT)}")
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError(f"invalid PNG chunk length: {path.relative_to(ROOT)}")
        chunk_type = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        expected_crc = struct.unpack(">I", data[offset + 8 + length:end])[0]
        actual_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise ValueError(f"PNG chunk CRC mismatch: {path.relative_to(ROOT)}")
        try:
            chunk_name = chunk_type.decode("ascii")
        except UnicodeDecodeError as exc:
            raise ValueError(f"invalid PNG chunk type: {path.relative_to(ROOT)}") from exc
        chunks.append(chunk_name)
        if chunk_type == b"IHDR":
            if ihdr is not None or length != 13:
                raise ValueError(f"invalid PNG IHDR: {path.relative_to(ROOT)}")
            ihdr = struct.unpack(">IIBBBBB", payload)
        elif chunk_type == b"IDAT":
            idat_parts.append(payload)
        offset = end
        if chunk_type == b"IEND":
            break

    if offset != len(data) or not chunks or chunks[-1] != "IEND":
        raise ValueError(f"PNG has trailing data or no IEND: {path.relative_to(ROOT)}")
    if chunks[0] != "IHDR" or chunks.count("IHDR") != 1 or chunks.count("IEND") != 1:
        raise ValueError(f"invalid PNG critical chunk order: {path.relative_to(ROOT)}")
    if not idat_parts or ihdr is None:
        raise ValueError(f"PNG is missing image data: {path.relative_to(ROOT)}")

    width, height, bit_depth, color_type, compression, filtering, interlace = ihdr
    if (bit_depth, color_type, compression, filtering, interlace) != (8, 2, 0, 0, 0):
        raise ValueError(f"social PNG must be non-interlaced 8-bit RGB: {path.relative_to(ROOT)}")
    try:
        pixels = zlib.decompress(b"".join(idat_parts))
    except zlib.error as exc:
        raise ValueError(f"PNG image data does not decompress: {path.relative_to(ROOT)}") from exc
    row_size = 1 + width * 3
    if len(pixels) != row_size * height:
        raise ValueError(f"PNG decompressed size is invalid: {path.relative_to(ROOT)}")
    if any(pixels[row * row_size] > 4 for row in range(height)):
        raise ValueError(f"PNG contains an invalid scanline filter: {path.relative_to(ROOT)}")

    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "chunks": chunks,
    }


def parse_html() -> tuple[SiteHTMLParser, str]:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    parser = SiteHTMLParser()
    parser.feed(html)
    parser.close()
    return parser, html


def project_files() -> set[str]:
    return {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(ROOT).parts
    }


def verify_inventory(errors: list[str]) -> None:
    actual = project_files()
    missing = EXPECTED_FILES - actual
    extra = actual - EXPECTED_FILES
    if missing:
        errors.append("missing required files: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("unexpected files: " + ", ".join(sorted(extra)))

    binary_files = {
        path for path in actual if (ROOT / path).read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    }
    approved_binary_files = set(SCREENSHOTS) | {SOCIAL_IMAGE_PATH}
    if binary_files != approved_binary_files:
        errors.append("binary scope differs from the four approved PNG assets")

    forbidden_parts = {"__pycache__", ".pytest_cache", "build", "dist", "htmlcov", ".venv"}
    artifacts = [path for path in actual if forbidden_parts.intersection(Path(path).parts)]
    artifacts.extend(path for path in actual if path.endswith((".pyc", ".pyo", ".log")))
    if artifacts:
        errors.append("generated artifacts present: " + ", ".join(sorted(artifacts)))


def verify_html(errors: list[str]) -> None:
    parser, html = parse_html()
    errors.extend(parser.errors)

    if parser.headings.count(1) != 1:
        errors.append("HTML must contain exactly one h1")
    if not parser.headings or parser.headings[0] != 1:
        errors.append("first heading must be h1")
    for previous, current in zip(parser.headings, parser.headings[1:]):
        if current > previous + 1:
            errors.append(f"heading level skips from h{previous} to h{current}")

    tag_names = [tag for tag, _ in parser.tags]
    for landmark in ("header", "nav", "main", "footer"):
        if landmark not in tag_names:
            errors.append(f"missing landmark: {landmark}")

    skip_links = [link for link in parser.links if "skip-link" in link.get("class", "").split()]
    if len(skip_links) != 1 or skip_links[0].get("href") != "#main-content":
        errors.append("skip link must resolve to #main-content")

    for link in parser.links:
        href = link.get("href", "")
        if not href:
            errors.append("anchor without href")
            continue
        if "target" in link:
            errors.append(f"target attribute is not approved: {href}")
        parsed = urlparse(href)
        if href.startswith("#"):
            if href[1:] not in parser.ids:
                errors.append(f"unresolved fragment: {href}")
        elif not parsed.scheme:
            local_path = ROOT / parsed.path
            if not local_path.is_file():
                errors.append(f"unresolved internal link: {href}")

    nav_fragments = {
        link.get("href", "")
        for tag, attrs in parser.tags
        if tag == "nav"
        for link in parser.links
        if link.get("href", "").startswith("#")
    }
    for fragment in nav_fragments:
        if fragment[1:] not in parser.ids:
            errors.append(f"navigation target does not resolve: {fragment}")

    link_tags = [attrs for tag, attrs in parser.tags if tag == "link"]
    canonical = [attrs.get("href") for attrs in link_tags if attrs.get("rel") == "canonical"]
    if canonical != [CANONICAL_URL]:
        errors.append("canonical URL is missing or incorrect")

    meta_by_name = {item.get("name"): item.get("content") for item in parser.metas if item.get("name")}
    if not meta_by_name.get("description"):
        errors.append("meta description is missing")
    if meta_by_name.get("viewport") != "width=device-width, initial-scale=1":
        errors.append("viewport metadata is incorrect")

    og = {item.get("property"): item.get("content") for item in parser.metas if item.get("property")}
    expected_og = {
        "og:title": SOCIAL_TITLE,
        "og:description": SOCIAL_DESCRIPTION,
        "og:type": "website",
        "og:url": CANONICAL_URL,
        "og:image": SOCIAL_IMAGE_URL,
        "og:image:width": str(SOCIAL_IMAGE["width"]),
        "og:image:height": str(SOCIAL_IMAGE["height"]),
        "og:image:alt": SOCIAL_IMAGE_ALT,
    }
    if og != expected_og:
        errors.append("Open Graph metadata differs from the approved social-preview set")

    expected_twitter = {
        "twitter:card": "summary_large_image",
        "twitter:title": SOCIAL_TITLE,
        "twitter:description": SOCIAL_DESCRIPTION,
        "twitter:image": SOCIAL_IMAGE_URL,
        "twitter:image:alt": SOCIAL_IMAGE_ALT,
    }
    twitter = {
        name: meta_by_name.get(name)
        for name in expected_twitter
    }
    if twitter != expected_twitter:
        errors.append("Twitter metadata differs from the approved social-preview set")
    og_description = og.get("og:description", "") or ""
    twitter_description = twitter.get("twitter:description", "") or ""
    if not og_description.strip() or og_description != twitter_description:
        errors.append("social descriptions must be nonempty and consistent")
    if html.count(SOCIAL_IMAGE_URL) != 2:
        errors.append("social image URL must appear exactly in Open Graph and Twitter metadata")

    if len(parser.scripts) != 1 or parser.scripts[0].get("type") != "application/ld+json":
        errors.append("only one non-executable JSON-LD script is allowed")
    else:
        try:
            person = json.loads(parser.scripts[0]["data"])
        except json.JSONDecodeError as exc:
            errors.append(f"JSON-LD does not parse: {exc}")
        else:
            approved_person = {
                "@context": "https://schema.org",
                "@type": "Person",
                "name": "David Mevorah",
                "jobTitle": "Healthcare integration engineer",
                "url": CANONICAL_URL,
                "sameAs": [GITHUB_PROFILE_URL, LINKEDIN_URL],
            }
            if person != approved_person:
                errors.append("JSON-LD contains unapproved or incorrect public fields")

    forbidden_tags = {"form", "iframe", "object", "embed", "video", "audio", "canvas"}
    found_forbidden = forbidden_tags.intersection(tag_names)
    if found_forbidden:
        errors.append("forbidden executable or embedded elements: " + ", ".join(sorted(found_forbidden)))

    external_resources: list[str] = []
    for tag, attrs in parser.tags:
        if tag in {"img", "script", "iframe", "source", "video", "audio"}:
            source = attrs.get("src", "")
            if source.startswith(("http://", "https://", "//")):
                external_resources.append(source)
        if tag == "link" and attrs.get("rel") in {"stylesheet", "preload", "modulepreload"}:
            href = attrs.get("href", "")
            if href.startswith(("http://", "https://", "//")):
                external_resources.append(href)
    if external_resources:
        errors.append("external runtime resources found: " + ", ".join(external_resources))

    outbound = {
        link["href"]
        for link in parser.links
        if link.get("href", "").startswith(("http://", "https://"))
    }
    approved_outbound = APPROVED_REPOSITORY_URLS | {GITHUB_PROFILE_URL, LINKEDIN_URL}
    if outbound != approved_outbound:
        errors.append("outbound links differ from the approved GitHub and LinkedIn set")

    for stale in (
        "https://github.com/mevorahde/ProjectCreationAutomation",
        "https://github.com/mevorahde/HyphyOregonConferences",
        "https://github.com/mevorahde/pw_locker_sql_local",
        "https://github.com/mevorahde/opening_multi_apps_gui",
    ):
        if stale in html:
            errors.append(f"obsolete repository URL found: {stale}")

    if re.search(r"\b\d+\s+(?:automated\s+)?tests?\b", html, re.IGNORECASE):
        errors.append("brittle exact test-count claim found")

    banned_employers = ("Cambia", "Clover Health", "Rula", "Sectra", "Optum", "Medtronic")
    for employer in banned_employers:
        if employer.lower() in html.lower():
            errors.append(f"unsupported employer content found: {employer}")

    if re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", html, re.IGNORECASE):
        errors.append("email address found in public HTML")
    if re.search(r"[A-Za-z]:\\Users\\", html):
        errors.append("machine-specific path found in public HTML")
    if re.search(r"(?i)(api[_-]?key|access[_-]?token|password)\s*[:=]\s*['\"][^'\"]+", html):
        errors.append("secret-like assignment found in public HTML")

    public_runtime_text = html + "\n" + (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
    environment_markers = (".env", "process.env", "os.environ", "environment variable")
    for marker in environment_markers:
        if marker.lower() in public_runtime_text.lower():
            errors.append(f"runtime environment reference found: {marker}")
    tracker_markers = (
        "google-analytics",
        "googletagmanager",
        "gtag(",
        "plausible.io",
        "matomo",
        "segment.com",
        "mixpanel",
        "hotjar",
        "facebook pixel",
        "tracking pixel",
    )
    for marker in tracker_markers:
        if marker.lower() in public_runtime_text.lower():
            errors.append(f"tracking or analytics library reference found: {marker}")
    if re.search(r"\b(?:resume|résumé)\b", html, re.IGNORECASE):
        errors.append("unsupported career-document content found")

    for image in parser.images:
        src = image.get("src", "")
        if not src or not (ROOT / src).is_file():
            errors.append(f"image path does not resolve: {src}")
        alt = image.get("alt", "").strip()
        if len(alt) < 20:
            errors.append(f"image alt text is not sufficiently descriptive: {src}")
        if not image.get("width", "").isdigit() or not image.get("height", "").isdigit():
            errors.append(f"image dimensions are missing: {src}")
        if image.get("loading") != "lazy":
            errors.append(f"below-the-fold image is not lazy-loaded: {src}")

    html_images = {image.get("src") for image in parser.images}
    if html_images != set(SCREENSHOTS):
        errors.append("HTML image set differs from the approved screenshots")


def verify_screenshots(errors: list[str]) -> None:
    parser, _ = parse_html()
    html_images = {image["src"]: image for image in parser.images if "src" in image}
    provenance = (ROOT / "ASSET_PROVENANCE.md").read_text(encoding="utf-8")
    for relative, expected in SCREENSHOTS.items():
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"approved screenshot missing: {relative}")
            continue
        actual_hash = sha256(path)
        if actual_hash != expected["sha256"]:
            errors.append(f"screenshot hash mismatch: {relative}")
        try:
            dimensions = png_dimensions(path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if dimensions != (expected["width"], expected["height"]):
            errors.append(f"screenshot dimensions mismatch: {relative}")
        html_image = html_images.get(relative, {})
        if html_image.get("width") != str(expected["width"]):
            errors.append(f"HTML width does not match PNG: {relative}")
        if html_image.get("height") != str(expected["height"]):
            errors.append(f"HTML height does not match PNG: {relative}")
        if relative not in provenance or expected["sha256"] not in provenance:
            errors.append(f"asset provenance is incomplete: {relative}")


def verify_social_image(errors: list[str]) -> None:
    path = ROOT / SOCIAL_IMAGE_PATH
    if not path.is_file():
        errors.append(f"approved social image missing: {SOCIAL_IMAGE_PATH}")
        return
    try:
        details = inspect_png(path)
    except ValueError as exc:
        errors.append(str(exc))
        return
    for field in ("width", "height", "bit_depth", "color_type"):
        if details[field] != SOCIAL_IMAGE[field]:
            errors.append(f"social image {field} mismatch")
    chunks = details["chunks"]
    if not isinstance(chunks, list) or set(chunks) != {"IHDR", "IDAT", "IEND"}:
        errors.append("social image contains ancillary, metadata, text, or private chunks")
    if sha256(path) != SOCIAL_IMAGE["sha256"]:
        errors.append("social image hash mismatch")
    provenance = (ROOT / "ASSET_PROVENANCE.md").read_text(encoding="utf-8")
    for evidence in (
        SOCIAL_IMAGE_PATH,
        str(SOCIAL_IMAGE["sha256"]),
        "1200 × 630",
        "Open Graph and LinkedIn",
        "David Mevorah owns",
    ):
        if evidence not in provenance:
            errors.append(f"social image provenance is incomplete: {evidence}")


def verify_supporting_files(errors: list[str]) -> None:
    robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
    expected_robots = (
        "User-agent: *\n"
        "Allow: /\n"
        "Sitemap: https://mevorahde.github.io/sitemap.xml\n"
    )
    if robots != expected_robots:
        errors.append("robots.txt content is incorrect")

    try:
        sitemap_tree = ET.parse(ROOT / "sitemap.xml")
    except ET.ParseError as exc:
        errors.append(f"sitemap XML does not parse: {exc}")
    else:
        namespace = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locations = [node.text for node in sitemap_tree.findall("s:url/s:loc", namespace)]
        if locations != [CANONICAL_URL]:
            errors.append("sitemap URL is incorrect")

    editor_text = (ROOT / ".editorconfig").read_text(encoding="utf-8")
    editor_parser = configparser.ConfigParser(interpolation=None, strict=True)
    try:
        editor_parser.read_string("[editorconfig]\n" + editor_text)
    except configparser.Error as exc:
        errors.append(f"EditorConfig does not parse: {exc}")
    else:
        if editor_parser["editorconfig"].get("root") != "true":
            errors.append("EditorConfig root setting is incorrect")
        if "*" not in editor_parser or editor_parser["*"].get("charset") != "utf-8":
            errors.append("EditorConfig UTF-8 setting is missing")

    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8").splitlines()
    parsed_attributes: list[tuple[str, list[str]]] = []
    for line_number, line in enumerate(attributes, start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) < 2:
            errors.append(f"invalid Git attributes line {line_number}")
        else:
            parsed_attributes.append((parts[0], parts[1:]))
    if ("*.png", ["binary"]) not in parsed_attributes:
        errors.append("Git attributes must mark PNG files as binary")
    if ("*", ["text=auto", "eol=lf"]) not in parsed_attributes:
        errors.append("Git attributes must define normalized LF text")

    css = (ROOT / "assets/css/site.css").read_text(encoding="utf-8")
    for requirement in (
        "@media (max-width: 42rem)",
        "@media (prefers-reduced-motion: reduce)",
        "@media (prefers-contrast: more)",
        "@media (forced-colors: active)",
        ":focus-visible",
    ):
        if requirement not in css:
            errors.append(f"responsive or accessibility CSS missing: {requirement}")
    if re.search(r"url\s*\(\s*['\"]?(?:https?:)?//", css, re.IGNORECASE):
        errors.append("external CSS resource found")


def verify_privacy_and_scope(errors: list[str]) -> None:
    textual_suffixes = {".html", ".css", ".md", ".txt", ".xml", ".py"}
    text_paths = [
        ROOT / relative
        for relative in project_files()
        if (ROOT / relative).suffix.lower() in textual_suffixes
        or (ROOT / relative).name in {"LICENSE", ".editorconfig", ".gitattributes", ".gitignore"}
    ]
    machine_path = re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE)
    email = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
    for path in text_paths:
        text = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        if machine_path.search(text):
            errors.append(f"machine-specific path found: {relative}")
        if relative not in {"tools/verify_site.py", "tests/test_site.py"} and email.search(text):
            errors.append(f"email address found in delivered content: {relative}")

    disallowed_extensions = {
        ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".pdf", ".doc", ".docx",
        ".xls", ".xlsx", ".db", ".sqlite", ".ico", ".svg", ".mp4", ".webm", ".zip", ".exe",
    }
    unsupported = [
        relative for relative in project_files() if (ROOT / relative).suffix.lower() in disallowed_extensions
    ]
    if unsupported:
        errors.append("unsupported file types found: " + ", ".join(sorted(unsupported)))


def run_checks() -> list[str]:
    errors: list[str] = []
    verify_inventory(errors)
    if (ROOT / "index.html").is_file():
        verify_html(errors)
    if all((ROOT / path).is_file() for path in SCREENSHOTS):
        verify_screenshots(errors)
    verify_social_image(errors)
    verify_supporting_files(errors)
    verify_privacy_and_scope(errors)
    return errors


def main() -> int:
    errors = run_checks()
    if errors:
        print("Site verification failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Site verification passed.")
    print(
        f"Verified {len(EXPECTED_FILES)} intended files, including three approved screenshots "
        "and one sanitized social-preview image."
    )
    print("HTML, metadata, links, assets, privacy boundaries, and repository text policies passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
