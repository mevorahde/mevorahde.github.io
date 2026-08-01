# David Mevorah portfolio

This repository contains the dependency-free static source for David Mevorah's
portfolio at <https://mevorahde.github.io/>.

The site uses semantic HTML and CSS, requires no build step, and is designed to
publish directly from the repository root with GitHub Pages. It contains no
runtime application, analytics, forms, cookies, external fonts, or embedded
third-party media.

## Local review

Open `index.html` directly in a browser when visual review is authorized. All
styles and images are local, so the page remains usable offline except for
ordinary outbound links.

Run the standard-library checks from the repository root:

```text
python -B -m unittest discover -s tests -p "test_*.py" -v
python -B tools/verify_site.py
```

No package installation or build command is required.

## Publication

The intended future destination is a public GitHub Pages user site published
from the root of the `main` branch. Repository creation, Pages configuration,
custom-domain configuration, and publication are deliberately outside this
local draft.

## Licensing and assets

Original website code is licensed under the MIT License. Linked repositories
retain their own licenses and attribution requirements. Copied screenshots do
not inherit the website-code license; their exact provenance and reuse decisions
are recorded in `ASSET_PROVENANCE.md`.
