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
hanyuc.com/          build output - only data/ is tracked; index.html and
                     static/ are generated and deliberately not committed
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

## Music

`content.yaml` holds Spotify track ids. Metadata and album art are fetched
once and committed, so the build never needs the network:

```sh
python refresh_music.py     # rewrites music.yaml + hanyuc.com/data/images/music/
```

Run it after changing the `music:` ids. A track with no cached entry still
renders (it falls back to showing the id), so forgetting cannot break a build.

The page ships no Spotify iframe. Clicking a track creates a single player via
Spotify's iFrame API and later clicks reuse it, so nothing is requested from
Spotify until you actually play something.

### Updating it automatically (not set up)

`top/tracks` and `recently-played` are user-scoped, so they need OAuth - which
cannot be done safely from a static page. The workable route is to do it in CI:

1. Create a Spotify app; authorise your own account once to get a refresh token.
2. Store `SPOTIFY_CLIENT_ID`, `SPOTIFY_CLIENT_SECRET` and
   `SPOTIFY_REFRESH_TOKEN` as GitHub Actions secrets.
3. Have a scheduled workflow exchange the refresh token for an access token,
   call `/v1/me/top/tracks?time_range=short_term&limit=6`, and rewrite
   `music.yaml` before building.

Prefer `top/tracks` over `recently-played`: the latter includes skips and
repeats. Two things to weigh first - it publishes your listening habits with no
curation step, and a failed token refresh should fall back to the committed
`music.yaml` rather than failing the deploy.

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
site from `content.yaml` and publishes `hanyuc.com/` to GitHub Pages.

The generated files (`hanyuc.com/index.html` and `hanyuc.com/static/`) are not
committed - CI produces them on every deploy. So a fresh clone has no site in
it until you run `python build.py`, and there is no committed copy that can
fall out of step with `content.yaml` or the stylesheet.

The pre-2026 version of this site is tagged `v1`.
