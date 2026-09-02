# hanyuc.com

Static personal site. Content is data, markup is templates, styling is one
stylesheet. No framework, no bundler, no JavaScript dependencies.

```
content.yaml         all site content - bio, publications, teaching, links
templates/
  base.html          <head>, meta tags, analytics
  index.html         page structure
  icons.html         inline SVG icon set
static/
  style.css          design tokens + layout + components
  fonts/             self-hosted woff2 (Newsreader, IBM Plex Mono, subset CJK)
build.py             renders templates -> hanyuc.com/
hanyuc.com/          published output; data/ holds PDFs and images
```

## Editing

Almost every change is a `content.yaml` change. To add a publication, append an
entry to `publications:` (newest first) and drop a thumbnail in
`hanyuc.com/data/images/thumbnails/`:

```yaml
  - id: my-paper
    title: A Paper About Something
    authors: [hanyu-chen, noah-snavely]     # keys from `people:`
    venue: IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)
    short_venue: CVPR                        # what actually renders
    year: 2027
    award: highlight                         # optional
    image: data/images/thumbnails/my_paper.png
    links:                                   # first link is the title's target
      - {type: project, href: "https://..."}
      - {type: pdf,     href: "data/papers/my_paper.pdf"}
      - {type: arxiv,   href: "https://arxiv.org/abs/..."}
```

A BibTeX entry is derived automatically. Set `journal: true` for `@article` or
`preprint: true` for `@misc`; add a literal `bibtex: |` block to override it
when you need volume/number/pages.

Unknown author keys and publications with no links fail the build rather than
rendering blank.

## Building

```sh
pip install -r requirements.txt
python build.py                 # writes hanyuc.com/index.html
python build.py --preview       # writes hanyuc.com/preview.html instead
```

Preview locally (needed for fonts - `file://` blocks them):

```sh
cd hanyuc.com && python -m http.server 8899
```

## Deploying

Pushing to `main` triggers `.github/workflows/deploy.yml`, which rebuilds the
site from `content.yaml` and publishes `hanyuc.com/` to GitHub Pages. Because
CI rebuilds, the deployed HTML cannot drift from the content it came from.

The pre-2026 version of this site is tagged `v1`.
