# David Mevorah portfolio

**View the live portfolio: <https://mevorahde.github.io/>**

This repository contains the dependency-free static source for David Mevorah's
public GitHub Pages user site. Its canonical URL is
<https://mevorahde.github.io/>.

The site uses semantic HTML and CSS, a responsive layout, accessibility-conscious
implementation, and local assets. It has no runtime dependencies or build step.
It includes no analytics, trackers, cookies, forms, external fonts, or embedded
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

This public GitHub Pages user site is published from the repository root of the
`main` branch. The canonical URL is <https://mevorahde.github.io/>.
The site does not use a custom domain.

## Licensing and assets

Original website code is licensed under the MIT License. Linked repositories
retain their own licenses and attribution requirements. Copied screenshots do
not inherit the website-code license; their exact provenance and reuse decisions
are recorded in `ASSET_PROVENANCE.md`.
