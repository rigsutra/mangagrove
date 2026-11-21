# MangaGrove site

Static Astro reader for [MangaGrove](https://mangagrove.ashishsingh92003.workers.dev): free webcomics in English and Hindi.

Source: https://github.com/rigsutra/mangagrove

## Layout

```text
public/series/<slug>/          cover.webp and page images (<lang>/ch-<n>/NN.webp)
src/data/series.json           series + chapter metadata (built by ../scripts/build_site_data.py)
src/lib/url.ts                 URL helpers, site name, language labels
src/layouts/Layout.astro       shared head (SEO, Open Graph, JSON-LD), header, footer, global CSS
src/pages/                     home, browse, series detail, chapter reader, 404
```

## Commands

Run from `site/`:

| Command           | Action                                  |
| :---------------- | :-------------------------------------- |
| `npm install`     | Install dependencies                    |
| `npm run dev`     | Dev server at `localhost:4321`          |
| `npm run build`   | Build to `./dist/`                      |
| `npm run preview` | Preview the build locally               |

## Deploy

- Primary: Cloudflare Worker `mangagrove` (`mangagrove.ashishsingh92003.workers.dev`), serving `./dist` per `wrangler.jsonc`.
- Mirror: GitHub Pages via `.github/workflows/deploy.yml` with `SITE_URL=https://rigsutra.github.io`, `SITE_BASE=/mangagrove` and `PUBLIC_NOINDEX=true`, so search engines index only the primary site.

`SITE_URL` and `SITE_BASE` override the defaults in `astro.config.mjs`.
