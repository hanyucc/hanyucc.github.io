# hanyuc.com

Source for my personal site. A small static-site generator: content is data,
markup is templates, styling is one stylesheet. No framework, no bundler, no
JavaScript dependencies.

```
content.yaml    bio, publications, teaching, links
templates/      Jinja2
static/         style.css and self-hosted fonts
build.py        renders one into the other
```

```sh
pip install -r requirements.txt
python build.py
```

Output lands in `hanyuc.com/` and is not committed — CI rebuilds it on every
push to `main` and publishes to GitHub Pages.

Feel free to borrow anything here. The previous version of the site is tagged
`v1`.
