# Asset provenance

Only the three project screenshots, one project demonstration video, one
social-preview image, and favicon system listed below are approved for this
portfolio site. Each project screenshot was copied byte-for-byte from a clean
checkout at the stated public commit. The social card and favicon artwork were
created specifically for this portfolio.

The website's MIT License covers original website code only. These screenshots
retain their source-project provenance and licensing context; their inclusion
does not imply that they inherit the website-code license.

## SQL Password Locker interface

- Portfolio path: `assets/images/sql-password-locker-interface.png`
- Original repository-relative path: `docs/images/sql-password-locker-gui.png`
- Source repository: <https://github.com/mevorahde/sql-password-locker>
- Source commit: `54b5e3b2d67d9beb5bf684050539456b433dddb5`
- Original SHA-256: `402633c3a545041972ca270e3eb298cbe596c7658a4d7e4ae83406bd5618bcf2`
- Copied SHA-256: `402633c3a545041972ca270e3eb298cbe596c7658a4d7e4ae83406bd5618bcf2`
- Dimensions: 895 × 625 pixels
- Reuse decision: Approved by the project owner for this portfolio. The image visibly identifies its accounts as synthetic. No broader or separate asset-license claim is made here.

## SQL Password Locker demonstration video

- Portfolio path: `assets/videos/sql-password-locker-demo.mp4`
- Source identifier: owner-reviewed local export, `SQL Password Locker Demo.mp4`
- Source SHA-256: `38237a48c902f0d3e44c73bc363fab1cb30a595b18b97abfba6c605dc56c7f13`
- Source size: 1,925,297 bytes
- Source streams: one 1440 × 1080 H.264/AVC video stream (39.266667 seconds, 1,178 frames, 30 fps) and one unused 48 kHz stereo AAC audio stream (39.242 seconds)
- Source metadata: ISO Base Media container brands plus a Clipchamp URL in the encoder field and a promotional Clipchamp URL/comment
- Processing: FFmpeg stream copy of the sole H.264 video stream, with audio, subtitles, attachments, data streams, chapters, inherited metadata, and nonessential source metadata excluded; fast-start layout places the `moov` atom before `mdat`. No video re-encoding or pixel alteration was performed.
- Video packet SHA-256 (source and final): `4750ad806154694df4db38739a4f76fba90b0be7adef6a6cac3de8a179627b63`
- Final streams: exactly one H.264/AVC `avc1` video stream using the `VideoHandler`; no audio, subtitle, attachment, or data streams
- Final dimensions and duration: 1440 × 1080 pixels; 39.266667 seconds
- Final metadata: ISO Base Media container brands and standard video handler/vendor fields only; no Clipchamp URL/comment, encoder, title, description, personal, machine, location, or creation-time metadata
- Final size: 959,618 bytes
- Final SHA-256: `400766cec39789ca797e517460a9def4d18570cda3a0657f948e7acef91718bf`
- Visual verification: Representative frames at the beginning, midpoint, and end were reviewed and match the approved source workflow; identical source/final video packet hashes additionally verify the copied H.264 payload.
- Content and reuse decision: Approved by the project owner for this portfolio. All visible account and credential information is synthetic portfolio data. No broader or separate asset-license claim is made here.

## Morning App Launcher interface

- Portfolio path: `assets/images/morning-app-launcher-interface.png`
- Original repository-relative path: `docs/images/morning-app-launcher.png`
- Source repository: <https://github.com/mevorahde/morning-app-launcher>
- Source commit: `cb718f787a14f32f2dcc3d8c3428b8afdcd61c4c`
- Original SHA-256: `ebe9f6e9294c17d4b53eee2f42ad3c024f3a34a4b51bea300ca93fe9a393c911`
- Copied SHA-256: `ebe9f6e9294c17d4b53eee2f42ad3c024f3a34a4b51bea300ca93fe9a393c911`
- Dimensions: 824 × 524 pixels
- Reuse decision: Approved by the project owner for this portfolio. The screenshot contains a harmless example application name. No separate asset-license claim is made here.

## Hyphy Oregon Conference Generator terminal

- Portfolio path: `assets/images/hyphy-oregon-conference-generator-terminal.png`
- Original repository-relative path: `docs/images/hyphy-oregon-conference-generator-cli.png`
- Source repository: <https://github.com/mevorahde/hyphy-oregon-conference-generator>
- Source commit: `14272f0f9e10b672e231dc81fafa19c15fd4b156`
- Original SHA-256: `4a9e4bd9a99d367726b44a986e1abd13e9f6331e1adcd3fb31eb16e32a128e9b`
- Copied SHA-256: `4a9e4bd9a99d367726b44a986e1abd13e9f6331e1adcd3fb31eb16e32a128e9b`
- Dimensions: 582 × 608 pixels
- Reuse decision: Approved by the project owner for this portfolio draft. It shows deterministic output captured from the functionally identical release candidate, not a separate final-release test.

## David Mevorah portfolio social preview

- Portfolio path: `assets/images/david-mevorah-portfolio-social-preview.png`
- Source identifier: generated image `019f57c4-3b9f-76c0-8344-34c29af199f1`, asset `exec-136e871c-0e7c-4fb3-a1be-0d06df7aa66a.png`
- Source dimensions: 1731 × 909 pixels
- Processing: Deterministic centered aspect-ratio fit using Lanczos resampling, with only the minimal top-and-bottom crop needed for the 1200:630 target ratio. The composition, colors, typography, and visible text were otherwise preserved.
- Sanitization: Re-encoded as RGB PNG with metadata, EXIF, text, comments, profiles, timestamps, machine paths, and private chunks removed.
- Final dimensions: 1200 × 630 pixels
- Final SHA-256: `8764c95d4d4f6698c24d3f86e8e81488c536baa0fb6d59379cc320dbbf794de3`
- Intended use: Open Graph and LinkedIn social preview for <https://mevorahde.github.io/>. The same image is also declared for compatible large-image social cards.
- Ownership and approval: David Mevorah owns the generated artwork and approves its use in this portfolio.

## David Mevorah portfolio favicon system

- Artwork: Created specifically for David Mevorah’s portfolio as an original deterministic vector design. No third-party artwork was incorporated.
- Design: A compact abstract DM systems mark using a deep-navy rounded square, warm-neutral D frame, muted-teal interconnected M, and restrained amber node.
- Source asset: `favicon.svg`; standalone SVG, 64 × 64 viewBox, SHA-256 `64b482e7290a1b35820b1ce3f66d21c1e622eac6683ca8a755f7545e55faf297`
- ICO derivative: `favicon.ico`; ICO with exactly three embedded 8-bit RGBA PNG frames at 16 × 16, 32 × 32, and 48 × 48 pixels; SHA-256 `6e7c912558d3aa69f6acd7c5d133ee6ead3cf75709b29f4f32651cdc52783df8`
- Apple touch derivative: `apple-touch-icon.png`; 180 × 180 pixels, 8-bit RGBA PNG; SHA-256 `d5f30e9592e361eb59ceb38e586d7ff3c6e7943400825e848a08f5d64892a7f0`
- Derivation: The ICO and PNG were deterministically rasterized from the SVG source design using only local, temporary standard-library tooling; the tooling was not added to the repository.
- Sanitization: Raster files contain only required image data and structural chunks, with metadata, comments, timestamps, text, profiles, EXIF, private chunks, and machine paths omitted.
- Ownership and approval: David owns the favicon artwork and approves its use with the portfolio.

No workbook material or unlisted binary asset is included in this portfolio.
