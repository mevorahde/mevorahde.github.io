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
VENV_GUIDE_URL = "https://mevorahde.github.io/venv_guide/"
FAVICON_SVG_PATH = "favicon.svg"
FAVICON_ICO_PATH = "favicon.ico"
APPLE_TOUCH_ICON_PATH = "apple-touch-icon.png"
SQL_VIDEO_PATH = "assets/videos/sql-password-locker-demo.mp4"
SQL_VIDEO_SHA256 = "400766cec39789ca797e517460a9def4d18570cda3a0657f948e7acef91718bf"
SQL_VIDEO_POSTER = "assets/images/sql-password-locker-interface.png"

EXPECTED_FILES = {
    ".editorconfig",
    ".gitattributes",
    ".gitignore",
    ".nojekyll",
    "ASSET_PROVENANCE.md",
    APPLE_TOUCH_ICON_PATH,
    "LICENSE",
    "README.md",
    "SECURITY.md",
    "assets/css/site.css",
    "assets/images/hyphy-oregon-conference-generator-terminal.png",
    "assets/images/morning-app-launcher-interface.png",
    "assets/images/sql-password-locker-interface.png",
    SQL_VIDEO_PATH,
    FAVICON_ICO_PATH,
    FAVICON_SVG_PATH,
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

FAVICON_ASSETS = {
    FAVICON_SVG_PATH: "64b482e7290a1b35820b1ce3f66d21c1e622eac6683ca8a755f7545e55faf297",
    FAVICON_ICO_PATH: "6e7c912558d3aa69f6acd7c5d133ee6ead3cf75709b29f4f32651cdc52783df8",
    APPLE_TOUCH_ICON_PATH: "d5f30e9592e361eb59ceb38e586d7ff3c6e7943400825e848a08f5d64892a7f0",
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
    if bit_depth != 8 or color_type not in {2, 6} or (compression, filtering, interlace) != (0, 0, 0):
        raise ValueError(f"PNG must be non-interlaced 8-bit RGB or RGBA: {path.relative_to(ROOT)}")
    try:
        pixels = zlib.decompress(b"".join(idat_parts))
    except zlib.error as exc:
        raise ValueError(f"PNG image data does not decompress: {path.relative_to(ROOT)}") from exc
    row_size = 1 + width * (3 if color_type == 2 else 4)
    if len(pixels) != row_size * height:
        raise ValueError(f"PNG decompressed size is invalid: {path.relative_to(ROOT)}")
    filter_types = [pixels[row * row_size] for row in range(height)]
    if any(filter_type > 4 for filter_type in filter_types):
        raise ValueError(f"PNG contains an invalid scanline filter: {path.relative_to(ROOT)}")

    has_transparency = None
    if color_type == 6 and set(filter_types) == {0}:
        has_transparency = any(
            pixels[row * row_size + 4 + column * 4] < 255
            for row in range(height)
            for column in range(width)
        )

    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "chunks": chunks,
        "filter_types": sorted(set(filter_types)),
        "has_transparency": has_transparency,
    }


def inspect_ico(path: Path) -> dict[str, object]:
    """Validate a metadata-free ICO containing only PNG-encoded RGBA frames."""

    data = path.read_bytes()
    if len(data) < 6:
        raise ValueError(f"truncated ICO: {path.relative_to(ROOT)}")
    reserved, image_type, count = struct.unpack_from("<HHH", data, 0)
    if (reserved, image_type, count) != (0, 1, 3):
        raise ValueError(f"ICO header or image count is invalid: {path.relative_to(ROOT)}")
    directory_end = 6 + count * 16
    frames: list[dict[str, object]] = []
    expected_offset = directory_end
    for index in range(count):
        width, height, colors, entry_reserved, planes, bits, size, offset = struct.unpack_from(
            "<BBBBHHII", data, 6 + index * 16
        )
        if 0 in (width, height) or colors != 0 or entry_reserved != 0 or planes != 1 or bits != 32:
            raise ValueError(f"ICO directory entry is invalid: {path.relative_to(ROOT)}")
        if offset != expected_offset or offset + size > len(data):
            raise ValueError(f"ICO frame offsets are invalid: {path.relative_to(ROOT)}")
        payload = data[offset:offset + size]
        if not payload.startswith(b"\x89PNG\r\n\x1a\n") or payload[12:16] != b"IHDR":
            raise ValueError(f"ICO frame is not PNG encoded: {path.relative_to(ROOT)}")
        png_width, png_height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
            ">IIBBBBB", payload[16:29]
        )
        chunks = []
        idat_parts = []
        png_offset = 8
        while png_offset < len(payload):
            length = struct.unpack(">I", payload[png_offset:png_offset + 4])[0]
            end = png_offset + 12 + length
            if end > len(payload):
                raise ValueError(f"ICO PNG frame is truncated: {path.relative_to(ROOT)}")
            kind = payload[png_offset + 4:png_offset + 8]
            expected_crc = struct.unpack(">I", payload[png_offset + 8 + length:end])[0]
            if zlib.crc32(kind + payload[png_offset + 8:png_offset + 8 + length]) & 0xFFFFFFFF != expected_crc:
                raise ValueError(f"ICO PNG frame CRC mismatch: {path.relative_to(ROOT)}")
            chunks.append(kind.decode("ascii"))
            if kind == b"IDAT":
                idat_parts.append(payload[png_offset + 8:png_offset + 8 + length])
            png_offset = end
        if png_offset != len(payload) or chunks != ["IHDR", "IDAT", "IEND"]:
            raise ValueError(f"ICO frame contains metadata or trailing data: {path.relative_to(ROOT)}")
        if (
            (png_width, png_height) != (width, height)
            or (bit_depth, color_type, compression, filtering, interlace) != (8, 6, 0, 0, 0)
        ):
            raise ValueError(f"ICO PNG frame dimensions or mode differ: {path.relative_to(ROOT)}")
        pixels = zlib.decompress(b"".join(idat_parts))
        row_size = 1 + width * 4
        if len(pixels) != row_size * height or any(pixels[row * row_size] != 0 for row in range(height)):
            raise ValueError(f"ICO PNG frame scanlines are not canonical: {path.relative_to(ROOT)}")
        has_transparency = any(
            pixels[row * row_size + 4 + column * 4] < 255
            for row in range(height)
            for column in range(width)
        )
        frames.append({"width": width, "height": height, "bit_depth": bit_depth, "color_type": color_type, "chunks": chunks, "has_transparency": has_transparency})
        expected_offset = offset + size
    if expected_offset != len(data):
        raise ValueError(f"ICO has trailing data: {path.relative_to(ROOT)}")
    return {"frames": frames}


def inspect_mp4(path: Path) -> dict[str, object]:
    """Return the structural facts needed to validate the reviewed MP4."""

    data = path.read_bytes()
    if len(data) < 16 or data[4:8] != b"ftyp":
        raise ValueError(f"invalid MP4 signature: {path.relative_to(ROOT)}")

    def boxes(start: int, end: int) -> list[tuple[bytes, int, int, int]]:
        found: list[tuple[bytes, int, int, int]] = []
        offset = start
        while offset < end:
            if offset + 8 > end:
                raise ValueError(f"truncated MP4 atom: {path.relative_to(ROOT)}")
            size = struct.unpack(">I", data[offset:offset + 4])[0]
            atom_type = data[offset + 4:offset + 8]
            header_size = 8
            if size == 1:
                if offset + 16 > end:
                    raise ValueError(f"truncated extended MP4 atom: {path.relative_to(ROOT)}")
                size = struct.unpack(">Q", data[offset + 8:offset + 16])[0]
                header_size = 16
            elif size == 0:
                size = end - offset
            if size < header_size or offset + size > end:
                raise ValueError(f"invalid MP4 atom length: {path.relative_to(ROOT)}")
            found.append((atom_type, offset, offset + header_size, offset + size))
            offset += size
        return found

    top_level = boxes(0, len(data))
    top_types = [atom_type.decode("latin-1") for atom_type, _, _, _ in top_level]
    moov = next((box for box in top_level if box[0] == b"moov"), None)
    if moov is None:
        raise ValueError(f"MP4 moov atom missing: {path.relative_to(ROOT)}")

    tracks: list[dict[str, object]] = []
    for trak in (box for box in boxes(moov[2], moov[3]) if box[0] == b"trak"):
        trak_children = boxes(trak[2], trak[3])
        tkhd = next((box for box in trak_children if box[0] == b"tkhd"), None)
        mdia = next((box for box in trak_children if box[0] == b"mdia"), None)
        if tkhd is None or mdia is None:
            raise ValueError(f"MP4 track structure is incomplete: {path.relative_to(ROOT)}")
        width_fixed, height_fixed = struct.unpack(">II", data[tkhd[3] - 8:tkhd[3]])
        mdia_children = boxes(mdia[2], mdia[3])
        hdlr = next((box for box in mdia_children if box[0] == b"hdlr"), None)
        mdhd = next((box for box in mdia_children if box[0] == b"mdhd"), None)
        minf = next((box for box in mdia_children if box[0] == b"minf"), None)
        if hdlr is None or mdhd is None or minf is None:
            raise ValueError(f"MP4 media structure is incomplete: {path.relative_to(ROOT)}")
        handler = data[hdlr[2] + 8:hdlr[2] + 12].decode("latin-1")
        version = data[mdhd[2]]
        timing_offset = mdhd[2] + (20 if version == 1 else 12)
        timescale = struct.unpack(">I", data[timing_offset:timing_offset + 4])[0]
        duration_size = 8 if version == 1 else 4
        duration = int.from_bytes(data[timing_offset + 4:timing_offset + 4 + duration_size], "big")
        minf_children = boxes(minf[2], minf[3])
        stbl = next((box for box in minf_children if box[0] == b"stbl"), None)
        if stbl is None:
            raise ValueError(f"MP4 sample table is missing: {path.relative_to(ROOT)}")
        stsd = next((box for box in boxes(stbl[2], stbl[3]) if box[0] == b"stsd"), None)
        if stsd is None or stsd[2] + 16 > stsd[3]:
            raise ValueError(f"MP4 sample description is missing: {path.relative_to(ROOT)}")
        codec = data[stsd[2] + 12:stsd[2] + 16].decode("latin-1")
        tracks.append({
            "handler": handler,
            "codec": codec,
            "width": width_fixed >> 16,
            "height": height_fixed >> 16,
            "duration": duration / timescale if timescale else 0,
        })

    return {
        "size": len(data),
        "top_level": top_types,
        "tracks": tracks,
        "moov_offset": moov[1],
        "mdat_offset": next((box[1] for box in top_level if box[0] == b"mdat"), -1),
        "has_video_handler_name": b"VideoHandler" in data,
        "lowercase_bytes": data.lower(),
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
    approved_binary_files = set(SCREENSHOTS) | {SOCIAL_IMAGE_PATH, APPLE_TOUCH_ICON_PATH}
    if binary_files != approved_binary_files:
        errors.append("PNG binary scope differs from the five approved PNG assets")

    mp4_files = {path for path in actual if (ROOT / path).read_bytes()[4:8] == b"ftyp"}
    if mp4_files != {SQL_VIDEO_PATH}:
        errors.append("MP4 binary scope differs from the one approved video asset")

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
            local_path = ROOT / parsed.path.lstrip("/")
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
    favicon_links = [
        attrs for attrs in link_tags
        if attrs.get("rel") in {"icon", "alternate icon", "apple-touch-icon"}
    ]
    expected_favicon_links = [
        {"rel": "icon", "type": "image/svg+xml", "href": "/favicon.svg"},
        {"rel": "alternate icon", "type": "image/x-icon", "href": "/favicon.ico"},
        {"rel": "apple-touch-icon", "sizes": "180x180", "href": "/apple-touch-icon.png"},
    ]
    if favicon_links != expected_favicon_links:
        errors.append("favicon link elements differ from the exact approved set")

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

    forbidden_tags = {"form", "iframe", "object", "embed", "audio", "canvas"}
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

    videos = [attrs for tag, attrs in parser.tags if tag == "video"]
    sources = [attrs for tag, attrs in parser.tags if tag == "source"]
    expected_video = {
        "controls": "",
        "preload": "metadata",
        "playsinline": "",
        "poster": SQL_VIDEO_POSTER,
        "aria-describedby": "sql-password-locker-demo-caption sql-password-locker-demo-transcript",
    }
    if videos != [expected_video]:
        errors.append("SQL Password Locker video attributes differ from the approved accessible set")
    if sources != [{"src": SQL_VIDEO_PATH, "type": "video/mp4"}]:
        errors.append("SQL Password Locker video source or MIME type is incorrect")
    if html.count(SQL_VIDEO_PATH) != 1:
        errors.append("SQL Password Locker video path must be referenced exactly once")
    if videos and any(attribute in videos[0] for attribute in ("autoplay", "loop")):
        errors.append("SQL Password Locker video must not autoplay or loop")
    transcript_requirements = (
        'id="sql-password-locker-demo-caption"',
        'id="sql-password-locker-demo-transcript"',
        "Approximately 39 seconds",
        "synthetic portfolio data",
        "credential creation",
        "encrypted persistence",
        "clipboard copying with automatic clearing",
        "deletion",
        "vault locking",
        "Read the video transcript",
    )
    for requirement in transcript_requirements:
        if requirement not in html:
            errors.append(f"SQL Password Locker video caption or transcript is incomplete: {requirement}")

    outbound = {
        link["href"]
        for link in parser.links
        if link.get("href", "").startswith(("http://", "https://"))
    }
    approved_outbound = APPROVED_REPOSITORY_URLS | {GITHUB_PROFILE_URL, LINKEDIN_URL, VENV_GUIDE_URL}
    if outbound != approved_outbound:
        errors.append("outbound links differ from the exact approved set")

    supporting_start = html.find('<section class="section supporting-section"')
    supporting_end = html.find("</section>", supporting_start)
    supporting_html = html[supporting_start:supporting_end] if supporting_start >= 0 and supporting_end >= 0 else ""
    git_heading = supporting_html.find("<h3>Git Cheat Sheet</h3>")
    python_heading = supporting_html.find("<h3>Python Virtual Environment Guide</h3>")
    if not supporting_html or git_heading < 0 or python_heading < 0 or git_heading >= python_heading:
        errors.append("supporting-work entries are missing or Git Cheat Sheet is not first")
    if html.count(VENV_GUIDE_URL) != 1 or supporting_html.count(VENV_GUIDE_URL) != 1:
        errors.append("Virtual Environment Guide URL must occur exactly once in supporting work")
    if supporting_html.count('<article class="supporting-card">') != 2:
        errors.append("supporting work must contain exactly two subordinate articles")

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
    expected_images = set(SCREENSHOTS) - {SQL_VIDEO_POSTER}
    if html_images != expected_images:
        errors.append("HTML image set differs from the approved displayed screenshots")


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
        if relative == SQL_VIDEO_POSTER:
            videos = [attrs for tag, attrs in parser.tags if tag == "video"]
            if len(videos) != 1 or videos[0].get("poster") != relative:
                errors.append(f"approved poster is not attached to the video: {relative}")
        else:
            html_image = html_images.get(relative, {})
            if html_image.get("width") != str(expected["width"]):
                errors.append(f"HTML width does not match PNG: {relative}")
            if html_image.get("height") != str(expected["height"]):
                errors.append(f"HTML height does not match PNG: {relative}")
        if relative not in provenance or expected["sha256"] not in provenance:
            errors.append(f"asset provenance is incomplete: {relative}")


def verify_sql_video(errors: list[str]) -> None:
    path = ROOT / SQL_VIDEO_PATH
    if not path.is_file():
        errors.append(f"approved video missing: {SQL_VIDEO_PATH}")
        return
    if sha256(path) != SQL_VIDEO_SHA256:
        errors.append("SQL Password Locker video hash mismatch")
    try:
        details = inspect_mp4(path)
    except ValueError as exc:
        errors.append(str(exc))
        return
    tracks = details["tracks"]
    if tracks != [{
        "handler": "vide",
        "codec": "avc1",
        "width": 1440,
        "height": 1080,
        "duration": 39.266666666666666,
    }]:
        errors.append("SQL Password Locker video track inventory or properties are incorrect")
    if not details["has_video_handler_name"]:
        errors.append("SQL Password Locker video handler name is missing")
    if not (500_000 <= details["size"] <= 2_000_000):
        errors.append("SQL Password Locker video size is outside the approved bound")
    if details["moov_offset"] < 0 or details["mdat_offset"] < 0 or details["moov_offset"] > details["mdat_offset"]:
        errors.append("SQL Password Locker video is not fast-start optimized")
    lower = details["lowercase_bytes"]
    forbidden_metadata = (
        b"clipchamp",
        b"http://",
        b"https://",
        b"comment",
        b"encoder",
        b"lavf",
        b"creation_time",
        b"location",
        b"com.apple.quicktime",
        b"c:\\users\\",
        b"/users/",
    )
    if any(marker in lower for marker in forbidden_metadata):
        errors.append("SQL Password Locker video contains URL, comment, private, or machine metadata")
    provenance = (ROOT / "ASSET_PROVENANCE.md").read_text(encoding="utf-8")
    for evidence in (SQL_VIDEO_PATH, SQL_VIDEO_SHA256, "39.266667", "1440 × 1080", "959,618 bytes"):
        if evidence not in provenance:
            errors.append(f"video provenance is incomplete: {evidence}")


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


def verify_favicons(errors: list[str]) -> None:
    provenance = (ROOT / "ASSET_PROVENANCE.md").read_text(encoding="utf-8")
    for relative, expected_hash in FAVICON_ASSETS.items():
        matches = [path for path in ROOT.rglob(Path(relative).name) if path.is_file()]
        if matches != [ROOT / relative]:
            errors.append(f"favicon asset must exist exactly once: {relative}")
            continue
        if sha256(matches[0]) != expected_hash:
            errors.append(f"favicon hash mismatch: {relative}")
        if relative not in provenance or expected_hash not in provenance:
            errors.append(f"favicon provenance is incomplete: {relative}")

    svg_path = ROOT / FAVICON_SVG_PATH
    if svg_path.is_file():
        svg_text = svg_path.read_text(encoding="utf-8")
        try:
            svg_root = ET.fromstring(svg_text)
        except ET.ParseError as exc:
            errors.append(f"favicon SVG does not parse: {exc}")
        else:
            namespace = "{http://www.w3.org/2000/svg}"
            if svg_root.tag != namespace + "svg" or svg_root.get("viewBox") != "0 0 64 64":
                errors.append("favicon SVG root or viewBox is invalid")
            titles = svg_root.findall(namespace + "title")
            if len(titles) != 1 or not (titles[0].text or "").strip():
                errors.append("favicon SVG must contain one descriptive title")
            allowed = {namespace + name for name in ("svg", "title", "rect", "path", "circle")}
            if any(element.tag not in allowed for element in svg_root.iter()):
                errors.append("favicon SVG contains an unapproved element")
            for element in svg_root.iter():
                for name, value in element.attrib.items():
                    if name.lower().endswith("href") or "url(" in value.lower() or value.startswith(("http:", "https:", "//")):
                        errors.append("favicon SVG contains an external reference")
        if "<script" in svg_text.lower() or "<!--" in svg_text or "<!doctype" in svg_text.lower():
            errors.append("favicon SVG contains script, comment, or document-type metadata")

    apple_path = ROOT / APPLE_TOUCH_ICON_PATH
    if apple_path.is_file():
        try:
            apple = inspect_png(apple_path)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            if (apple["width"], apple["height"], apple["bit_depth"], apple["color_type"]) != (180, 180, 8, 6):
                errors.append("Apple touch icon must be exactly 180x180 8-bit RGBA")
            if apple["chunks"] != ["IHDR", "IDAT", "IEND"]:
                errors.append("Apple touch icon contains metadata, ancillary, or private chunks")
            if apple["filter_types"] != [0] or apple["has_transparency"] is not True:
                errors.append("Apple touch icon must use canonical scanlines and transparent outer pixels")

    ico_path = ROOT / FAVICON_ICO_PATH
    if ico_path.is_file():
        try:
            ico = inspect_ico(ico_path)
        except ValueError as exc:
            errors.append(str(exc))
        else:
            frames = ico["frames"]
            if [(frame["width"], frame["height"]) for frame in frames] != [(16, 16), (32, 32), (48, 48)]:
                errors.append("ICO frame inventory must be exactly 16, 32, and 48 pixels")
            if not all(frame["has_transparency"] is True for frame in frames):
                errors.append("every ICO frame must contain transparent outer pixels")


def verify_readme(errors: list[str]) -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    required = (
        "**View the live portfolio: <https://mevorahde.github.io/>**",
        "public GitHub Pages user site",
        "repository root of the\n`main` branch",
        "does not use a custom domain",
        "semantic HTML and CSS",
        "responsive layout",
        "accessibility-conscious",
        "local assets",
        "no runtime dependencies or build step",
        "no analytics, trackers, cookies, forms, external fonts, or embedded\nthird-party media",
    )
    for phrase in required:
        if phrase not in readme:
            errors.append(f"README publication or architecture fact missing: {phrase}")
    for stale in ("intended future destination", "local draft", "future destination"):
        if stale.lower() in readme.lower():
            errors.append(f"README contains stale publication wording: {stale}")


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
    if ("*.ico", ["binary"]) not in parsed_attributes:
        errors.append("Git attributes must mark ICO files as binary")
    if ("*.mp4", ["binary"]) not in parsed_attributes:
        errors.append("Git attributes must mark MP4 files as binary")
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
        ".xls", ".xlsx", ".db", ".sqlite", ".webm", ".zip", ".exe",
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
    verify_sql_video(errors)
    verify_social_image(errors)
    verify_favicons(errors)
    verify_supporting_files(errors)
    verify_readme(errors)
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
        f"Verified {len(EXPECTED_FILES)} intended files, including three approved screenshots, "
        "one reviewed video, one sanitized social-preview image, and three original favicon assets."
    )
    print("HTML, metadata, links, assets, privacy boundaries, and repository text policies passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
